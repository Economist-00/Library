from django import forms
from django.core.exceptions import ValidationError
from .models import Book

class IsbnForm(forms.Form):
    isbn = forms.CharField(help_text="ISBN", max_length=13, widget=forms.TextInput(attrs={'placeholder': 'Enter 13-digit ISBN'}))

    def clean_isbn(self):
        data = self.cleaned_data['isbn']
        if len(data) != 13:
            raise ValidationError("Invalid code - ISBN has to be 13 digits")
        
        return data


class CreateBookForm(forms.ModelForm):
    storage_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'enter storage name'}), help_text="create a new storage location for this copy")
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author', 'publish_date', 'image_url']
        widgets = {
            'isbn': forms.HiddenInput(),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'publish_date': forms.TextInput(attrs={'class': 'form-control'}),
            'image_url': forms.HiddenInput(),
        }