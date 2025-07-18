from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from registration_book.models import Book, BookInstance
from accounts.models import Employee
# Create your models here.


class Loan(models.Model):
    loan_id = models.AutoField('貸出状況ID', primary_key=True)
    book_instance = models.ForeignKey(BookInstance, on_delete=models.CASCADE, related_name='loan')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans')
    loan_start = models.DateField('貸出開始日', null=True, blank=True)
    due_date = models.DateField('返却予定日', null=True, blank=True)
    return_date = models.DateField('返却日', null=True, blank=True)
    
    @property
    def loaned(self):
        return bool(self.loan_start) and self.return_date is None

    @property
    def overdue(self):
        return bool(self.due_date) and not self.return_date and self.due_date < timezone.now().date()

    def clean(self):
        # Only validate if both dates are provided
        if self.loan_start and self.due_date:
            if self.loan_start >= self.due_date:
                raise ValidationError("You cannot return a book before renting it.")

            max_due_date = self.loan_start + timedelta(weeks=2)
            if self.due_date > max_due_date:
                raise ValidationError("Due date cannot be more than 2 weeks from loan start date.")
    
    def __str__(self):
        status = 'Returned' if self.return_date else 'On Loan'
        return f'{self.employee.username} renting {self.book_instance.book.title} ({status})'
    
    class Meta:
        # enforce only one active loan per instance
        constraints = [
            models.UniqueConstraint(
                fields=['book_instance'],
                condition=models.Q(return_date__isnull=True),
                name='unique_active_loan_per_instance'
            )
        ]

class Reservation(models.Model):
    reserve_id = models.AutoField('予約状況ID', primary_key=True)
    book_instance = models.ForeignKey(BookInstance, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    future_rent = models.DateField('予約開始日', null=True, blank=True)
    future_return = models.DateField('予約返却日', null=True, blank=True)

    def clean(self):
        if self.future_rent >= self.future_return:
            raise ValidationError("Invalid reservation period.")
        overlapping = Reservation.objects.filter(
            book_instance=self.book_instance,
            future_rent__lt=self.future_return,
            future_return__gt=self.future_rent
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("This book instance is already reserved for the selected period.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['book_instance', 'employee'],
                name='unique_reservation_per_user_per_instance'
            )
        ]
        
    def __str__(self):
        return f"{self.employee.username} reserved '{self.book_instance.book.title}' from {self.future_rent} to {self.future_return}"


class Review(models.Model):
    review_id = models.AutoField('レビューID', primary_key=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    scores = [(i, str(i)) for i in range(1, 6)]
    score = models.IntegerField('評価値', choices=scores, null=True, blank=True)
    review_title = models.CharField('レビュータイトル', max_length=20, null=True, blank=True)
    review = models.TextField('レビュー', null=True, blank=True)
    date = models.DateField('レビュー日', null=True, blank=True)

    class Meta:
        unique_together = ('book', 'employee')

    def __str__(self):
        return f"{self.employee.username} reviewed '{self.book.title}' ({self.score}/5): {self.review_title}"
