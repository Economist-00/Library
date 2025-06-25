from django.db import models
from django.contrib.auth.models import AbstractUser

from registration_book.models import Book, BookInstance

# Create your models here.


# class Rental(models.Model):
#     rental_id = models.AutoField('貸出状況ID', primary_key=True)
#     book_instance = models.OneToOneField(BookInstance, on_delete=models.CASCADE)
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
#     rent_start = models.DateField()
#     due_date = models.DateField()
#     return_date = models.DateField()
#     on_rent = models.BooleanField(default=False)
#     over_due = models.BooleanField(default=False)

#     def __str__(self):
#         return f'{self.employee.username} : {self.book_instance.book.title}'
    

class Reservation(models.Model):
    pass



class Review(models.Model):
    pass