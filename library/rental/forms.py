from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Reservation, Loan, Review
import re


class BookInstanceSearchForm(forms.Form):
    isbn = forms.CharField(
        label='ISBN', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    title = forms.CharField(
        label='Title', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    author = forms.CharField(
        label='Author', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def clean_isbn(self):
        data = self.cleaned_data.get('isbn', '').strip()
        if not data:
            return data
        
        # Require exactly 13 digits, no letters or special chars
        if not re.fullmatch(r'\d{13}', data):
            raise ValidationError("Enter a full 13-digit ISBN number.")
        return data


class DeleteAccountForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        # Check that the entered username matches the logged-in user
        if username != self.user.username:
            raise forms.ValidationError("The username does not match your account.")

        # Verify the password against the user's actual password hash
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password. Please try again.")
        return cleaned_data


class RentForm(forms.Form):
    due_date = forms.DateField(
        label='Due Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': date.today().isoformat(),
            'max': (date.today() + timedelta(weeks=2)).isoformat(),
            'class': 'form-control'
        })
    )

    def __init__(self, *args, book_instance=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.book_instance = book_instance
        self.user = user

    def clean_due_date(self):
        due = self.cleaned_data['due_date']
        today = date.today()
        
        # Basic date validation
        if due < today:
            raise forms.ValidationError("Due date cannot be in the past.")
        if due > today + timedelta(weeks=2):
            raise forms.ValidationError("Due date must be within two weeks.")
        
        return due

    def clean(self):
        cleaned = super().clean()
        due_date = cleaned.get('due_date')
        
        if not self.book_instance:
            raise ValidationError("Book instance is required.")
        
        if not due_date:
            return cleaned
        
        today = date.today()
        
        # Check for overlapping reservations
        overlapping_reservations = Reservation.objects.filter(
            book_instance=self.book_instance,
            future_rent__lte=due_date,  # Reservation starts before or on rental end date
            future_return__gte=today    # Reservation ends after or on rental start date
        )
        
        if overlapping_reservations.exists():
            first_conflict = overlapping_reservations.order_by('future_rent').first()
            raise ValidationError(
                f"Cannot rent until {due_date} because this copy is reserved "
                f"from {first_conflict.future_rent} to {first_conflict.future_return} "
                f"by {first_conflict.employee.username}. "
                f"Please choose an earlier due date or rent after the reservation period."
            )
        
        active_loans = Loan.objects.filter(employee=self.user, return_date__isnull=True).count()
        if active_loans >= 10:
            raise ValidationError(
                "You cannot rent more than 10 books at a time. Please return a book before renting another."
            )

        return cleaned
   
    
class ReservationForm(forms.Form):
    future_rent = forms.DateField(
        label="Reservation Start",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    future_return = forms.DateField(
        label="Reservation End",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    def __init__(self, *args, book_instance=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.book_instance = book_instance
        self.user = user

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("future_rent")
        end = cleaned.get("future_return")

        if not self.book_instance:
            raise ValidationError("Book instance is required.")
        
        if not self.user:
            raise ValidationError("User is required.")

        today = date.today()

        # 1. Check if user already has a reservation for this specific book instance
        existing_reservation = Reservation.objects.filter(
            book_instance=self.book_instance,
            employee=self.user,
            future_return__gte=today  # Only check future/active reservations
        ).first()

        if existing_reservation:
            raise ValidationError(
                f"You already have a reservation for this book copy from "
                f"{existing_reservation.future_rent} to {existing_reservation.future_return}. "
                f"Please cancel or wait for your current reservation to expire before making a new one."
            )

        # 2. Check if user already has a reservation for ANY copy of this book
        existing_book_reservation = Reservation.objects.filter(
            book_instance__book=self.book_instance.book,
            employee=self.user,
            future_return__gte=today
        ).first()

        if existing_book_reservation:
            raise ValidationError(
                f"You already have a reservation for another copy of '{self.book_instance.book.title}' "
                f"(Copy {existing_book_reservation.book_instance.book_instance_id}) from "
                f"{existing_book_reservation.future_rent} to {existing_book_reservation.future_return}. "
                f"Please cancel or wait for your current reservation to expire before making a new one."
            )

        # 3. Check if user is currently borrowing this book instance
        active_loan = Loan.objects.filter(
            book_instance=self.book_instance,
            employee=self.user,
            return_date__isnull=True
        ).first()

        if active_loan:
            raise ValidationError(
                f"You are currently borrowing this book (due: {active_loan.due_date}). "
                f"Please return it before making a reservation."
            )

        # 4. Check if user is currently borrowing ANY copy of this book
        active_loan_same_book = Loan.objects.filter(
            book_instance__book=self.book_instance.book,
            employee=self.user,
            return_date__isnull=True
        ).first()

        if active_loan_same_book:
            raise ValidationError(
                f"You are currently borrowing another copy of '{self.book_instance.book.title}' "
                f"(Copy {active_loan_same_book.book_instance.book_instance_id}, due: {active_loan_same_book.due_date}). "
                f"Please return it before making a reservation."
            )

        # 5. Existing validation for availability, date ranges, etc.
        active_loans = Loan.objects.filter(
            book_instance=self.book_instance, 
            return_date__isnull=True
        )
        
        if active_loans.exists():
            latest_due_date = max(loan.due_date for loan in active_loans)
            available_from = latest_due_date + timedelta(days=1)
        else:
            available_from = today

        active_resvs = Reservation.objects.filter(
            book_instance=self.book_instance, 
            future_return__gt=today
        ).exclude(employee=self.user)  # Exclude current user's reservations
        
        last_resv_end = max((res.future_return for res in active_resvs), default=today)
        available_from = max(available_from, last_resv_end + timedelta(days=1))

        if start < available_from:
            raise ValidationError(f"Reservations can begin no earlier than {available_from}")

        if end > start + timedelta(weeks=2):
            raise ValidationError("Reservation cannot extend beyond two weeks from its start date.")

        if start >= end:
            raise ValidationError("End date must come after start date.")

        # # 6. Enforce max 3 active reservations for this instance (excluding current user)
        # overlapping = Reservation.objects.filter(
        #     book_instance=self.book_instance,
        #     future_rent__lt=end,
        #     future_return__gt=start
        # ).exclude(employee=self.user)

        # if overlapping.count() >= 3:
        #     raise ValidationError("This copy already has three overlapping reservations.")

        return cleaned
    

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review_title', 'score', 'review']
        widgets = {
            'review_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter review title'}),
            'score': forms.Select(choices=[(i, f'{i} stars') for i in range(1, 6)], attrs={'class': 'form-control'}),
            'review': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your review here...'}),
        }
        labels = {
            'review_title': 'Review Title',
            'score': 'Rating',
            'review': 'Your Review',
        }
