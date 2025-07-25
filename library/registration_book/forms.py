from django import forms
from django.core.exceptions import ValidationError
from .models import Book, BookInstance, Storage

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
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publish_date', 'subject']
    
    storage = forms.CharField(
        label="Storage Location",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter or select a storage"})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    
    def clean(self):
        """
        Override clean method to prevent unique constraint validation
        since we handle book creation/retrieval in the view with get_or_create
        """
        # Get cleaned data without calling super().clean()
        # This prevents the unique_together validation from running
        cleaned_data = {}
        for field_name, field in self.fields.items():
            if field_name != 'storage':  # Skip storage field as it's not part of Book model
                try:
                    cleaned_data[field_name] = field.clean(self.data.get(field_name))
                except ValidationError:
                    # If individual field validation fails, add the error
                    self.add_error(field_name, field.error_messages.get('invalid', 'Invalid value'))
        
        # Add storage field separately
        storage_field = self.fields['storage']
        try:
            cleaned_data['storage'] = storage_field.clean(self.data.get('storage'))
        except ValidationError:
            self.add_error('storage', 'Please select a valid storage location')
        
        return cleaned_data

    

class BookConfirmationForm(forms.Form):
    isbn = forms.CharField(max_length=13, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255, required=False)
    publish_date = forms.CharField(max_length=15, required=False)
    subject = forms.CharField(widget=forms.Textarea, required=False)
    image_url = forms.URLField(required=False)
    storage_name = forms.CharField(max_length=255)  
