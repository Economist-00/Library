from django.shortcuts import render
from .models import Rental, Reservation, Review
from registration_book.models import Book, BookInstance
# Create your views here.

# def book_search(request):
#     if request.method == "POST":
#         query
#         return render(request, 'rental_app/search_results.html')
#     return render(request, 'rental_app/book_search.html')
