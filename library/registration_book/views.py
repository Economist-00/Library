import requests
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views import generic
from django.db import transaction, IntegrityError
from django.urls import reverse
from .forms import IsbnForm, CreateBookForm, BookInstanceSearchForm
from .models import Book, BookInstance, Storage
# Create your views here.

def index(request):
    return render(request, 'registration_book/index.html')

def isbn_input_view(request):
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
                summary = book.get('summary', {})
                return {
                    'title': summary.get('title', ''),
                    'author': summary.get('author', ''),
                    'publish_date': summary.get('pubdate', ''),
                    'image_url': summary.get('cover', '')
                }
    except Exception as e:
        print(f"API error: {e}")
    return None

def book_confirmation_view(request):
    book_data = request.session.get('book_data')
    if not book_data:
        return redirect('isbn_input')
    initial_data = book_data.copy()
    initial_data['isbn'] = book_data.get('isbn', '')

    if request.method == 'POST':
        form = CreateBookForm(request.POST, initial=initial_data)
        if form.is_valid():
            storage_name = form.cleaned_data.pop('storage_name')
            try:
                with transaction.atomic():
                    book, _ = Book.objects.update_or_create(
                        isbn=book_data['isbn'],
                        defaults=form.cleaned_data
                    )
                    storage, _ = Storage.objects.get_or_create(
                        storage_name=storage_name
                    )
                    BookInstance.objects.create(
                        book=book,
                        storage=storage
                    )
                    del request.session['book_data']
                    return redirect('registration_complete')  # <-- Only here!
            except IntegrityError as e:
                messages.error(request, f'Database error: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error saving record: {str(e)}')
    else:
        form = CreateBookForm(initial=initial_data)

    return render(request, 'registration_book/book_confirmation.html', {
        'form': form,
        'book_data': book_data
    })

def registration_complete_view(request):
    return render(request, 'registration_book/registration_complete.html')


def book_instance_search(request):
    form = BookInstanceSearchForm(request.GET or None)
    book = None
    instances = None

    # Only search if ISBN parameter exists and form is valid
    if request.GET.get('isbn') and form.is_valid():
        isbn = form.cleaned_data['isbn']
        try:
            book = Book.objects.get(isbn=isbn)
            instances = book.instances.all().select_related('storage')
        except Book.DoesNotExist:
            # book remains None, template will handle the "not found" message
            pass

    return render(request, 'registration_book/book_instance_search.html', {
        'form': form,
        'book': book,
        'instances': instances,
    })


def book_instance_delete(request, pk):
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

def delete_complete(request):
    """Renders the delete completion page."""
    return render(request, 'registration_book/delete_complete.html')