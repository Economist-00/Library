import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.views import generic
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.urls import reverse
from .forms import IsbnForm, BookInstanceSearchForm, ManualBookForm, BookConfirmationForm
from .models import Book, BookInstance, Storage
# Create your views here.

@login_required(login_url='/accounts/librarian/login/')
def reg_index(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    return render(request, 'registration_book/reg_index.html')

@login_required(login_url='/accounts/librarian/login/')
def isbn_input_view(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    if request.method == 'POST':
        form = IsbnForm(request.POST)
        if form.is_valid():
            isbn = form.cleaned_data['isbn']
            
            # Fetch book data from OpenBD API
            book_data = fetch_book_from_openbd(isbn)
            
            if book_data:
                # Store book data in session for next step
                book_data['isbn'] = isbn  # Add ISBN to session data
                request.session['book_data'] = book_data
                return redirect('book_confirmation')
            else:
                messages.error(request, 'Book not found in OpenBD database')
    else:
        form = IsbnForm()
    
    return render(request, 'registration_book/isbn_input.html', {'form': form})
   
def fetch_book_from_openbd(isbn):
    try:
        url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data and data[0]:
                book = data[0]

                book_info = {
                    'isbn': isbn,
                    'title': '',
                    'author': '',
                    'publish_date': '',
                    'subject': '',
                    'image_url': ''
                }

                # Extract from 'summary'
                if 'summary' in book:
                    summary = book['summary']
                    book_info.update({
                        'title': summary.get('title', ''),
                        'author': summary.get('author', ''),
                        'publish_date': summary.get('pubdate', ''),
                        'image_url': summary.get('cover', '') or 'https://www.svgrepo.com/show/83343/book.svg'
                    })

                # Extract 'subject' from ONIX if available
                try:
                    descriptive_detail = book.get('onix', {}).get('DescriptiveDetail', {})
                    subject_data = descriptive_detail.get('Subject')

                    subject_list = []

                    if isinstance(subject_data, dict):
                        subject_text = subject_data.get('SubjectHeadingText') or subject_data.get('SubjectCode')
                        if subject_text:
                            subject_list.append(subject_text)

                    elif isinstance(subject_data, list):
                        for item in subject_data:
                            subject_text = item.get('SubjectHeadingText') or item.get('SubjectCode')
                            if subject_text:
                                subject_list.append(subject_text)

                    if subject_list:
                        book_info['subject'] = '; '.join(subject_list)

                except Exception as e:
                    print(f"Subject extraction error: {e}")
                    book_info['subject'] = ''

                return book_info

    except Exception as e:
        print(f"OpenBD API error: {e}")

    return None

@login_required(login_url='/accounts/librarian/login/')
def manual_book_registration(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    if request.method == 'POST':
        form = ManualBookForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    book = form.save(commit=False)
                    if not book.image_url:
                        book.image_url = 'https://www.svgrepo.com/show/83343/book.svg'
                    book.save()

                    storage_name = form.cleaned_data['storage_name']
                    storage, _ = Storage.objects.get_or_create(storage_name=storage_name)

                    BookInstance.objects.create(book=book, storage=storage)

                    messages.success(request, 'Book registered successfully.')
                    return redirect('complete_manual')

            except Exception as e:
                messages.error(request, f'Error: {e}')

    else:
        form = ManualBookForm()

    return render(request, 'registration_book/manual_book_registration.html', {'form': form})

@login_required
def registration_complete_manual(request):
    if request.user.user_type != 'librarian':
        return redirect('librarian_login')

    return render(request, 'registration_book/registration_complete_manual.html')

@login_required(login_url='/accounts/librarian/login/')
def book_confirmation_view(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    book_data = request.session.get('book_data')
    if not book_data:
        return redirect('isbn_input')

    if request.method == 'POST':
        form = BookConfirmationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Check if book exists
                    book, _ = Book.objects.get_or_create(
                        isbn=form.cleaned_data['isbn'],
                        defaults={
                            'title': form.cleaned_data['title'],
                            'author': form.cleaned_data['author'],
                            'publish_date': form.cleaned_data['publish_date'],
                            'subject': form.cleaned_data['subject'],
                            'image_url': form.cleaned_data['image_url'] or 'https://www.svgrepo.com/show/83343/book.svg'
                        }
                    )

                    # Create or get storage
                    storage, _ = Storage.objects.get_or_create(
                        storage_name=form.cleaned_data['storage_name']
                    )

                    # Create BookInstance (a physical copy)
                    BookInstance.objects.create(
                        book=book,
                        storage=storage
                    )

                    # Clear session data
                    del request.session['book_data']

                    return redirect('registration_complete')

            except Exception as e:
                messages.error(request, f'Error: {e}')

    else:
        form = BookConfirmationForm(initial={
            'isbn': book_data.get('isbn'),
            'title': book_data.get('title'),
            'author': book_data.get('author'),
            'publish_date': book_data.get('publish_date'),
            'subject': book_data.get('subject'),
            'image_url': book_data.get('image_url'),
        })

    return render(request, 'registration_book/book_confirmation.html', {
        'form': form
    })

@login_required(login_url='/accounts/librarian/login/')
def registration_complete_view(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    return render(request, 'registration_book/registration_complete.html')

@login_required(login_url='/accounts/librarian/login/')
def delete_book_instance_search(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    form = BookInstanceSearchForm(request.GET or None)
    instances = None

    if form.is_valid():
        isbn = form.cleaned_data.get('isbn', '').strip()
        title = form.cleaned_data.get('title', '').strip()
        if isbn or title:
            query = Q()
            if isbn:
                query |= Q(book__isbn__icontains=isbn)
            if title:
                query |= Q(book__title__icontains=title)
            instances = BookInstance.objects.filter(query).select_related('book', 'storage')
        else:
            instances = []

    return render(request, 'registration_book/delete_book_instance_search.html', {
        'form': form,
        'instances': instances,
    })

@login_required(login_url='/accounts/librarian/login/')
def book_instance_delete(request, pk):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    instance = get_object_or_404(BookInstance, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            book = instance.book
            instance.delete()
            if not book.instances.exists():
                book.delete()
        messages.success(request, 'Book instance—and book if orphaned—deleted successfully!')
        return redirect('delete_complete')  # Redirect to confirmation page
    return render(request, 'registration_book/book_instance_delete.html', {
        'instance': instance
    })

@login_required(login_url='/accounts/librarian/login/')
def delete_complete(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'librarian':
        return redirect('/accounts/librarian/login/')
    """Renders the delete completion page."""
    return render(request, 'registration_book/delete_complete.html')

def registration_book_logout(request):
    logout(request)
    return redirect('librarian_login')