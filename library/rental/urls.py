from django.urls import path
from . import views


urlpatterns = [
    path('search/', views.book_search, name='book_search'),
    path('book/<int:book_id>/'),
    path('rent/<uuid:book_instance_id>/'),
    path('reserve/'),
    path('dashboard'),
    path('return'),
    path('delete-account'),
]