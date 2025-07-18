from django.urls import path
from .views import rental_index, rental_logout
from . import views

urlpatterns = [
    path('', rental_index, name='rental_index'),
    path('search/', views.book_instance_search, name='book_instance_search'),
    path('results/', views.book_instance_results, name='book_instance_results'),
    path('logout/', rental_logout, name='rental_logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('instance/<str:instance_id>/', views.book_instance_detail, name='book_instance_detail'),
    path('instance/<str:instance_id>/rent/', views.rent_with_due_date, name='rent_with_due_date'),
    path('create-loan/', views.create_loan, name='create_loan'),
    path('instance/<str:instance_id>/reserve/', views.reserve_book, name='reserve_book'),
    path('cancel_reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('loan-history/', views.loan_history, name='loan_history'),
    path('loan/<int:loan_id>/return/', views.return_and_review, name='return_and_review'),
    path('loan/return/completed/', views.loan_return_completed, name='loan_return_completed'),
]