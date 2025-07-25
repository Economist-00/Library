from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg, Count, BooleanField, ExpressionWrapper
from django.db import IntegrityError, transaction
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from datetime import date, timedelta
import logging
from urllib.parse import urlencode
from .models import Loan, Reservation, Review
from registration_book.models import Book, BookInstance
from .forms import BookInstanceSearchForm, DeleteAccountForm, RentForm, ReservationForm, ReviewForm
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

    # Determine sort field and direction
    sort = request.GET.get('sort', 'title')   # default sort key
    direction = request.GET.get('dir', 'asc') # 'asc' or 'desc'
    sort_prefix = '' if direction == 'asc' else '-'
    # Map allowed sort keys to model fields
    sort_fields = {
        'title': 'book__title',
        'author': 'book__author',
        'isbn': 'book__isbn',
        'storage': 'storage__name',  # adjust to your storage field
    }
    order_by = sort_prefix + sort_fields.get(sort, 'book__title')

    if form.is_valid():
        isbn = form.cleaned_data.get('isbn', '').strip()
        title = form.cleaned_data.get('title', '').strip()
        author = form.cleaned_data.get('author', '').strip()

        # Build search query
        if isbn or title or author:
            query = Q()
            if isbn:
                query |= Q(book__isbn__icontains=isbn)
            if title:
                query |= Q(book__title__icontains=title)
            if author:
                query |= Q(book__author__icontains=author)
            instances = BookInstance.objects.filter(query)
        else:
            instances = BookInstance.objects.all()

        # Apply related selects, sorting, and pagination
        instances = (
            instances
            .select_related('book', 'storage')
            .order_by(order_by)
        )
        paginator = Paginator(instances, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    return render(request, 'rental/book_instance_results.html', {
        'form': form,
        'instances': instances,
        'page_obj': page_obj,
        'current_sort': sort,
        'current_dir': direction,
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
    
    book_instance = get_object_or_404(BookInstance, book_instance_id=instance_id)
    book = book_instance.book
    
    # Check if this instance is currently on loan
    current_loan = None
    is_available = True
    try:
        current_loan = Loan.objects.get(book_instance=book_instance, return_date__isnull=True)
        is_available = False
    except Loan.DoesNotExist:
        is_available = True

    # Get the latest reservation for this specific book instance
    latest_reservation = Reservation.objects.filter(
        book_instance=book_instance
    ).order_by('-future_return').first()

    # Check if user has existing reservations for this book
    user_reservation_this_instance = Reservation.objects.filter(
        book_instance=book_instance,
        employee=request.user,
        future_return__gte=date.today()
    ).first()
    
    user_reservation_any_copy = Reservation.objects.filter(
        book_instance__book=book,
        employee=request.user,
        future_return__gte=date.today()
    ).first()
    
    # Check if user is currently borrowing this specific instance
    user_has_this_instance = Loan.objects.filter(
        book_instance=book_instance,
        employee=request.user,
        return_date__isnull=True
    ).exists()

    # Check if user is currently borrowing any copy of this book
    user_has_any_copy = Loan.objects.filter(
        book_instance__book=book,
        employee=request.user,
        return_date__isnull=True
    ).exists()

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
    
    # Get reviews and other data...
    reviews = Review.objects.filter(book=book).select_related('employee').order_by('-date')
    avg_rating = reviews.aggregate(Avg('score'))['score__avg']
    rating_counts = reviews.values('score').annotate(count=Count('score')).order_by('score')
    
    # Get latest reservation
    latest_reservation = Reservation.objects.filter(
        book_instance=book_instance
    ).order_by('-future_return').first()

    
    
    context = {
        'book_instance': book_instance,
        'book': book,
        'current_loan': current_loan,
        'is_available': is_available,
        'latest_reservation': latest_reservation,
        'user_reservation_this_instance': user_reservation_this_instance,
        'user_reservation_any_copy': user_reservation_any_copy,
        'user_has_this_instance': user_has_this_instance,
        'user_has_any_copy': user_has_any_copy,
        'all_instances': all_instances,
        'available_instances': available_instances,
        'loaned_instances': loaned_instances,
        'total_copies': all_instances.count(),
        'available_count': len(available_instances),
        'reviews': reviews,
        'avg_rating': avg_rating,
        'rating_counts': rating_counts,
        'latest_reservation': latest_reservation,
        'user_can_rent': is_available and not user_has_any_copy,
        'user_can_reserve': not is_available and not user_has_any_copy,
    }
    
    return render(request, 'rental/book_instance_detail.html', context)



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
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')

    book_instance = get_object_or_404(BookInstance, book_instance_id=instance_id)
    
    # Prevent renting if already on loan
    if Loan.objects.filter(book_instance=book_instance, return_date__isnull=True).exists():
        messages.error(request, "This copy is already on loan.")
        return redirect('book_instance_detail', instance_id=instance_id)

    if request.method == 'POST':
        form = RentForm(request.POST, book_instance=book_instance)
        if form.is_valid():
            MAX_ACTIVE_LOANS = 10

            active_loans_count = Loan.objects.filter(employee=request.user, return_date__isnull=True).count()

            if active_loans_count >= MAX_ACTIVE_LOANS:
                form.add_error(None, "You cannot rent more than 10 books at once. Please return a book before renting another.")
                # Render the same page with form errors and message
                return render(request, 'rental/rent_with_due_date.html', {
                    'form': form,
                    'book_instance': book_instance
                })
            due = form.cleaned_data['due_date']
            
            # Double-check for reservation conflicts (in case of race conditions)
            today = date.today()
            overlapping_reservations = Reservation.objects.filter(
                book_instance=book_instance,
                future_rent__lte=due,
                future_return__gte=today
            )
            
            if overlapping_reservations.exists():
                first_conflict = overlapping_reservations.order_by('future_rent').first()
                messages.error(
                    request,
                    f"Cannot rent until {due} because this copy is reserved "
                    f"from {first_conflict.future_rent} to {first_conflict.future_return}. "
                    f"Please choose an earlier due date."
                )
                return render(request, 'rental/rent_with_due_date.html', {
                    'form': form,
                    'book_instance': book_instance
                })
            
            # Safe to create the loan
            try:
                Loan.objects.create(
                    book_instance=book_instance,
                    employee=request.user,
                    loan_start=today,
                    due_date=due
                )
                return render(request, 'rental/rental_complete.html', {
                    'book': book_instance.book,
                    'book_instance': book_instance,
                })
            except IntegrityError:
                messages.error(request, "Unable to rent this copy; it's already on loan.")
                return redirect('book_instance_detail', instance_id=instance_id)
    else:
        form = RentForm(book_instance=book_instance)

    return render(request, 'rental/rent_with_due_date.html', {
        'form': form,
        'book_instance': book_instance
    })


@login_required(login_url='/accounts/employee/login/')
def reserve_book(request, instance_id):
    if request.user.user_type != 'employee':
        return redirect('employee_login')

    book_instance = get_object_or_404(BookInstance, book_instance_id=instance_id)
    
    if request.method == "POST":
        form = ReservationForm(request.POST, book_instance=book_instance, user=request.user)
        if form.is_valid():
            res = Reservation.objects.create(
                book_instance=book_instance,
                employee=request.user,
                future_rent=form.cleaned_data["future_rent"],
                future_return=form.cleaned_data["future_return"]
            )
            messages.success(request,
                f"Reserved '{book_instance.book.title}' from {res.future_rent} to {res.future_return}.")
            return render(request, 'rental/reservation_complete.html', {
                'book': book_instance.book,
                'book_instance': book_instance,
                'reservation': res,  
            })

    else:
        form = ReservationForm(book_instance=book_instance, user=request.user)

    return render(request, "rental/reserve_book.html", {
        "form": form,
        "book_instance": book_instance,
        "instance_id": instance_id
    })


@login_required(login_url='/accounts/employee/login/')
def cancel_reservation(request, reservation_id):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    
    reservation = get_object_or_404(Reservation, reserve_id=reservation_id, employee=request.user)
    
    if request.method == 'POST':
        book_title = reservation.book_instance.book.title
        reservation.delete()
        messages.success(request, f'Your reservation for "{book_title}" has been cancelled.')
        return redirect('loan_history')
    
    return render(request, 'rental/cancel_reservation.html', {'reservation': reservation})

@login_required(login_url='/accounts/employee/login/')
def loan_history(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    
    # Get all loans and reservations for the current user
    loans = Loan.objects.filter(employee=request.user).select_related('book_instance__book', 'book_instance__storage').annotate(
            is_active=ExpressionWrapper(
                Q(return_date__isnull=True),
                output_field=BooleanField()
            )
        ).order_by('-is_active', '-loan_start')
    reservations = Reservation.objects.filter(employee=request.user).select_related('book_instance__book', 'book_instance__storage').order_by('-future_rent')
    
    # Count overdue books
    overdue_loans = loans.filter(return_date__isnull=True, due_date__lt=date.today())
    overdue_count = overdue_loans.count()
    
    # Pagination for loans
    paginator = Paginator(loans, 10)  # Show 10 loans per page
    page_number = request.GET.get('page')
    page_loans = paginator.get_page(page_number)
    
    context = {
        'loans': page_loans,
        'reservations': reservations,
        'overdue_count': overdue_count,
        'overdue_loans': overdue_loans,
    }
    
    return render(request, 'rental/loan_history.html', context)


def process_waiting_reservations_for_book(book_instance):
    """
    Process any waiting reservations when a book is returned
    """
    
    logger = logging.getLogger(__name__)
    today = timezone.localdate()
    
    # Find reservations waiting for this specific book
    waiting_reservations = Reservation.objects.filter(
        book_instance=book_instance,
        future_rent__lte=today
    ).order_by('future_rent')  # First come, first served
    
    if not waiting_reservations.exists():
        return
    
    # Process the first waiting reservation
    next_reservation = waiting_reservations.first()
    
    try:
        with transaction.atomic():
            # Create loan for the waiting user
            loan = Loan.objects.create(
                instance=next_reservation.book_instance,
                borrower=next_reservation.employee,
                start_date=today,
                due_date=next_reservation.future_return,
            )
            
            # Delete the reservation
            next_reservation.delete()
            
            logger.info(f"✅ Auto-processed waiting reservation {next_reservation.reserve_id} → loan {loan.loan_id}")
            
    except Exception as e:
        logger.error(f"Error auto-processing waiting reservation: {e}")

@login_required(login_url='/accounts/employee/login/')
def return_and_review(request, loan_id):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    
    loan = get_object_or_404(Loan, loan_id=loan_id, employee=request.user, return_date__isnull=True)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Handle review creation/update
            existing_review = Review.objects.filter(book=loan.book_instance.book, employee=request.user).first()
            
            if existing_review:
                existing_review.review_title = form.cleaned_data['review_title']
                existing_review.score = form.cleaned_data['score']
                existing_review.review = form.cleaned_data['review']
                existing_review.date = date.today()
                existing_review.save()
            else:
                review = form.save(commit=False)
                review.book = loan.book_instance.book
                review.employee = request.user
                review.date = date.today()
                review.save()
            
            # Mark loan as returned
            loan.return_date = date.today()
            loan.save()

            process_waiting_reservations_for_book(loan.book_instance)
            
            messages.success(request, f'Book "{loan.book_instance.book.title}" returned successfully and your review has been saved!')
            return redirect('loan_return_completed')
    else:
        existing_review = Review.objects.filter(book=loan.book_instance.book, employee=request.user).first()
        form = ReviewForm(instance=existing_review) if existing_review else ReviewForm()
    
    context = {
        'loan': loan,
        'form': form,
        'existing_review': Review.objects.filter(book=loan.book_instance.book, employee=request.user).first(),
    }
    
    return render(request, 'rental/return_and_review.html', context)


@login_required(login_url='/accounts/employee/login/')
def loan_return_completed(request):
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'employee':
        return redirect('/accounts/employee/login/')
    
    return render(request, 'rental/loan_return_completed.html')
