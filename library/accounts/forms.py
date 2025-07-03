# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser


class EmployeeLoginForm(AuthenticationForm):
    """Allows only users with user_type='employee' to log in."""
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if getattr(user, 'user_type', None) != 'employee':
            raise ValidationError(
                "This account is not an employee account.",
                code='invalid_login'
            )

class LibrarianLoginForm(AuthenticationForm):
    """Allows only users with user_type='librarian' to log in."""
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if getattr(user, 'user_type', None) != 'librarian':
            raise ValidationError(
                "This account is not a librarian account.",
                code='invalid_login'
            )

class CustomUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'user_type', 'password1', 'password2')

class EmployeeCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'employee'
        if commit:
            user.save()
        return user

class LibrarianCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'librarian'
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})
