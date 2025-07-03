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


class BookInstanceForm(forms.Form):
    storage_name = forms.CharField(
        max_length=255,
        label='Storage Location',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter storage location'
        }))

class BookInstanceSearchForm(forms.Form):
    isbn = forms.CharField(label='ISBN', required=False, max_length=13)
    title = forms.CharField(label='Book Title', required=False)
    
    
class ManualBookForm(forms.ModelForm):
    storage_name = forms.CharField(
        label="Storage Location",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter storage location'})
    )

    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author', 'publish_date', 'subject', 'image_url']
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'publish_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYYMM or YYYY'}),
            'subject': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional image URL'}),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        if isbn:
            if len(isbn) != 13:
                raise forms.ValidationError('ISBN must be 13 digits if provided.')
        return isbn


# class BookEditForm(forms.ModelForm):
#     storage_name = forms.CharField(
#         label="Storage Location",
#         max_length=255,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter storage location'})
#     )

#     class Meta:
#         model = Book
#         fields = ['isbn', 'title', 'author', 'publish_date', 'subject', 'image_url']
#         widgets = {
#             'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
#             'title': forms.TextInput(attrs={'class': 'form-control'}),
#             'author': forms.TextInput(attrs={'class': 'form-control'}),
#             'publish_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM'}),
#             'subject': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
#             'image_url': forms.TextInput(attrs={'class': 'form-control'}),
#         }

#     def clean_isbn(self):
#         isbn = self.cleaned_data.get('isbn')
#         if isbn:
#             if len(isbn) != 13:
#                 raise forms.ValidationError('ISBN must be 13 digits if provided.')
#         return isbn
    

class BookConfirmationForm(forms.Form):
    isbn = forms.CharField(max_length=13, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255, required=False)
    publish_date = forms.CharField(max_length=15, required=False)
    subject = forms.CharField(widget=forms.Textarea, required=False)
    image_url = forms.URLField(required=False)
    storage_name = forms.CharField(max_length=255)  # For the BookInstance
