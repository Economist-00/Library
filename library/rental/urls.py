from django.urls import path
from .views import rental_index, rental_logout
from . import views

urlpatterns = [
    path('', rental_index, name='rental_index'),
    path('search/', views.book_instance_search, name='book_instance_search'),
    path('results/', views.book_instance_results, name='book_instance_results'),
    path('logout/', rental_logout, name='rental_logout'),
    # path('book/<int:book_id>/'),
    # path('rent/<uuid:book_instance_id>/'),
    # path('reserve/'),
    # path('dashboard/'),
    # path('return/'),
    # path('delete-account'),
]