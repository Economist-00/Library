from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from datetime import date
from .models import Loan, Reservation, Review
from registration_book.models import Book, BookInstance
from .forms import BookInstanceSearchForm, DeleteAccountForm, RentForm
# Create your views here.

def employee_required(view_func):
    """
    Decorator: only allow access if user.user_type == 'employee'.
    Redirects others to the employee login.
    """
    from functools import wraps
    from django.urls import reverse_lazy

    @wraps(view_func)
    @login_required(login_url=reverse_lazy('accounts:employee_login'))
    def _wrapped(request, *args, **kwargs):
        if getattr(request.user, 'user_type', None) != 'employee':
            return redirect('accounts:employee_login')
        return view_func(request, *args, **kwargs)
    return _wrapped

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


@employee_required
def delete_account(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST, user=request.user)
        if form.is_valid():
            # Delete the employee’s user account
            request.user.delete()
            logout(request)
            messages.success(request, "Your account has been deleted.")
            return redirect('employee_login')
    else:
        form = DeleteAccountForm(user=request.user)
    return render(request, 'rental/delete_account.html', {'form': form})


@login_required(login_url='/accounts/employee/login/')
def book_instance_detail(request, instance_id):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    
    # Get the specific book instance
    book_instance = get_object_or_404(BookInstance, book_instance_id=instance_id)
    
    # Get the related book for reviews
    book = book_instance.book
    
    # Check if this instance is currently on loan
    current_loan = None
    is_available = True
    try:
        current_loan = Loan.objects.get(book_instance=book_instance, return_date__isnull=True)
        is_available = False
    except Loan.DoesNotExist:
        is_available = True
    
    # Get reviews for the book (not the instance)
    reviews = Review.objects.filter(book=book).select_related('employee').order_by('-date')
    
    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('score'))['score__avg']
    
    # Count reviews by rating
    rating_counts = reviews.values('score').annotate(count=Count('score')).order_by('score')
    
    # Get all instances of this book to show availability across copies
    all_instances = BookInstance.objects.filter(book=book).select_related('storage')
    available_instances = []
    loaned_instances = []
    
    for instance in all_instances:
        try:
            loan = Loan.objects.get(book_instance=instance, return_date__isnull=True)
            loaned_instances.append({
                'instance': instance,
                'loan': loan
            })
        except Loan.DoesNotExist:
            available_instances.append(instance)
    
    context = {
        'book_instance': book_instance,
        'book': book,
        'current_loan': current_loan,
        'is_available': is_available,
        'available_instances': available_instances,
        'loaned_instances': loaned_instances,
        'total_copies': all_instances.count(),
        'available_count': len(available_instances),
        'reviews': reviews,
        'avg_rating': avg_rating,
        'rating_counts': rating_counts,
        'user_can_rent': is_available,
    }
    
    return render(request, 'rental/book_instance_detail.html', context)


# rental/views.py
@login_required(login_url='/accounts/employee/login/')
def create_loan(request):
    if request.method == 'POST':
        if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
            return redirect('/accounts/employee/login/')
        
        book_instance_id = request.POST.get('book_instance_id')
        book_instance = get_object_or_404(BookInstance, book_instance_id=book_instance_id)
        
        # Check if instance is available
        existing_loan = Loan.objects.filter(book_instance=book_instance, return_date__isnull=True).first()
        if existing_loan:
            messages.error(request, 'This book copy is already on loan.')
            return redirect('book_instance_detail', instance_id=book_instance_id)
        
        # Create loan
        from datetime import date, timedelta
        loan = Loan.objects.create(
            book_instance=book_instance,
            employee=request.user,
            loan_start=date.today(),
            due_date=date.today() + timedelta(weeks=2)
        )
        
        messages.success(request, f'You have successfully rented "{book_instance.book.title}" (Copy {book_instance_id}). Due date: {loan.due_date}')
        return redirect('rental_index')
    
    return redirect('rental_index')


@login_required(login_url='/accounts/employee/login/')
def rent_with_due_date(request, instance_id):
    # Restrict to employees
    if getattr(request.user, 'user_type', None) != 'employee':
        return redirect('accounts:employee_login')

    book_instance = get_object_or_404(BookInstance, book_instance_id=instance_id)

    # Prevent renting if already on loan
    if Loan.objects.filter(book_instance=book_instance, return_date__isnull=True).exists():
        messages.error(request, "This copy is not available.")
        return redirect('book_instance_detail', instance_id=instance_id)

    if request.method == 'POST':
        form = RentForm(request.POST)
        if form.is_valid():
            due = form.cleaned_data['due_date']
            Loan.objects.create(
                book_instance=book_instance,
                employee=request.user,
                loan_start=date.today(),
                due_date=due
            )
            messages.success(request,
                f'You have rented "{book_instance.book.title}" (Copy {instance_id}). Due: {due}')
            return redirect('rental_index')
    else:
        form = RentForm()

    return render(request, 'rental/rent_with_due_date.html', {
        'form': form,
        'book_instance': book_instance
    })