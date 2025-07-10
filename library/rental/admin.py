from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Loan, Reservation, Review

# Register your models here.
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        'loan_id', 
        'book_title', 
        'employee_username', 
        'loan_start', 
        'due_date', 
        'return_date',
        'loan_status',
        'is_overdue'
    ]
    list_filter = [
        'loan_start', 
        'due_date', 
        'return_date'
    ]
    search_fields = [
        'book_instance__book__title',
        'book_instance__book__author', 
        'employee__username',
        'book_instance__book__isbn'
    ]
    list_editable = [
        'return_date'
    ]
    readonly_fields = [
        'loan_id',
        'is_overdue',
        'loan_status'
    ]
    ordering = ['-loan_start']
    date_hierarchy = 'loan_start'
    
    # Custom display methods
    def book_title(self, obj):
        return obj.book_instance.book.title
    book_title.short_description = 'Book Title'
    book_title.admin_order_field = 'book_instance__book__title'
    
    def employee_username(self, obj):
        return obj.employee.username
    employee_username.short_description = 'Employee'
    employee_username.admin_order_field = 'employee__username'
    
    def loan_status(self, obj):
        if obj.return_date:
            return format_html('<span style="color: green;">Returned</span>')
        elif obj.overdue:
            return format_html('<span style="color: red;">Overdue</span>')
        else:
            return format_html('<span style="color: orange;">On Loan</span>')
    loan_status.short_description = 'Status'
    
    def is_overdue(self, obj):
        return obj.overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

    # Optimize queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'book_instance__book', 
            'employee'
        )

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'reserve_id',
        'book_title',
        'employee_username',
        'future_rent',
        'future_return',
        'reservation_duration',
        'storage_location'
    ]
    list_filter = [
        'future_rent',
        'future_return',
        'book_instance__storage'
    ]
    search_fields = [
        'book_instance__book__title',
        'book_instance__book__author',
        'employee__username',
        'book_instance__book__isbn'
    ]
    list_editable = [
        'future_rent',
        'future_return'
    ]
    readonly_fields = [
        'reserve_id',
        'reservation_duration'
    ]
    ordering = ['-future_rent']
    date_hierarchy = 'future_rent'
    
    # Custom display methods
    def book_title(self, obj):
        return obj.book_instance.book.title
    book_title.short_description = 'Book Title'
    book_title.admin_order_field = 'book_instance__book__title'
    
    def employee_username(self, obj):
        return obj.employee.username
    employee_username.short_description = 'Employee'
    employee_username.admin_order_field = 'employee__username'
    
    def storage_location(self, obj):
        return obj.book_instance.storage.storage_name
    storage_location.short_description = 'Storage Location'
    storage_location.admin_order_field = 'book_instance__storage__storage_name'
    
    def reservation_duration(self, obj):
        if obj.future_rent and obj.future_return:
            duration = obj.future_return - obj.future_rent
            return f"{duration.days} days"
        return "N/A"
    reservation_duration.short_description = 'Duration'

    # Optimize queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'book_instance__book',
            'book_instance__storage',
            'employee'
        )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'review_id',
        'book_title',
        'employee_username',
        'review_title',
        'score',
        'date',
        'review_preview'
    ]
    list_filter = [
        'score',
        'date',
        'book__subject'
    ]
    search_fields = [
        'book__title',
        'book__author',
        'employee__username',
        'review_title',
        'review'
    ]
    list_editable = [
        'score',
        'review_title'
    ]
    readonly_fields = [
        'review_id'
    ]
    ordering = ['-date']
    date_hierarchy = 'date'
    
    # Custom display methods
    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = 'Book Title'
    book_title.admin_order_field = 'book__title'
    
    def employee_username(self, obj):
        return obj.employee.username
    employee_username.short_description = 'Employee'
    employee_username.admin_order_field = 'employee__username'
    
    def score_display(self, obj):
        stars = '★' * obj.score + '☆' * (5 - obj.score)
        return format_html(f'<span style="color: #ffc107;">{stars}</span> ({obj.score}/5)')
    score_display.short_description = 'Rating'
    score_display.admin_order_field = 'score'
    
    def review_preview(self, obj):
        if obj.review:
            return obj.review[:50] + "..." if len(obj.review) > 50 else obj.review
        return "No review text"
    review_preview.short_description = 'Review Preview'

    # Optimize queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'book',
            'employee'
        )