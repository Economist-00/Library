from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
# from .models import Rental, Reservation, Review
from registration_book.models import Book, BookInstance
from .forms import BookInstanceSearchForm
# Create your views here.

@login_required(login_url='/accounts/employee/login/')
def rental_index(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    return render(request, 'rental/rental_index.html')

@login_required(login_url='/accounts/employee/login/')
def book_instance_search(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    form = BookInstanceSearchForm(request.GET)
    return render(request, 'rental/book_instance_search.html', {'form': form})

@login_required(login_url='/accounts/employee/login/')
def book_instance_results(request):
    form = BookInstanceSearchForm(request.GET)
    instances = None
    page_obj = None

    if form.is_valid():
        isbn = form.cleaned_data.get('isbn', '').strip()
        title = form.cleaned_data.get('title', '').strip()
        author = form.cleaned_data.get('author', '').strip()

        # If any search criteria is provided, filter accordingly
        if isbn or title or author:
            query = Q()
            if isbn:
                query |= Q(book__isbn__icontains=isbn)
            if title:
                query |= Q(book__title__icontains=title)
            if author:
                query |= Q(book__author__icontains=author)
            instances = BookInstance.objects.filter(query).select_related('book', 'storage')
        else:
            # If no search criteria provided (blank query), return all book instances
            instances = BookInstance.objects.all().select_related('book', 'storage')
        
        # Apply pagination to the results
        paginator = Paginator(instances, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    
    return render(request, 'rental/book_instance_results.html', {
        'form': form,
        'instances': instances,
        'page_obj': page_obj,
    })


def rental_logout(request):
    logout(request)
    return redirect('employee_login')