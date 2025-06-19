from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('isbn_input/', views.isbn_input_view, name='isbn_input'),
    path('confirm/', views.book_confirmation_view, name='book_confirmation'),
    path('complete/', views.registration_complete_view, name='registration_complete'),
]