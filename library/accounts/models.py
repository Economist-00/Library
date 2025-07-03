# accounts/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('employee', 'Employee'),
        ('librarian', 'Librarian'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(_('email address'), blank=True)

    # Use the default UserManager to restore standard createsuperuser behavior
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'user_type']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


# Proxy models for better admin organization
class EmployeeManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type='employee')

class LibrarianManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type='librarian')

class Employee(CustomUser):
    objects = EmployeeManager()

    def save(self, *args, **kwargs):
        self.user_type = 'employee'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

class Librarian(CustomUser):
    objects = LibrarianManager()

    def save(self, *args, **kwargs):
        self.user_type = 'librarian'
        super().save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = 'Librarian'
        verbose_name_plural = 'Librarians'
