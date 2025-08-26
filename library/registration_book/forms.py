from django import forms
from django.core.exceptions import ValidationError
import datetime
from .models import Book


def validate_publish_date(value):
    """
    Allow 'YYYY-MM-DD' or 'YYYY' or 'YYYYMM' formats for publish_date.
    Raises ValidationError if not valid.
    """
    if not value:
        return 

    value = value.strip()
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return
    except ValueError:
        pass

    # Year only YYYY
    if len(value) == 4 and value.isdigit():
        return

    # Year+month YYYYMM
    if len(value) == 6 and value.isdigit():
        year = int(value[:4])
        month = int(value[4:6])
        if 1 <= month <= 12:
            return

    raise ValidationError(
        "Enter a valid publish date: YYYYMMDD, YYYY, or YYYYMM"
    )

class IsbnForm(forms.Form):
    isbn = forms.CharField(help_text="ISBN", max_length=13, widget=forms.TextInput(attrs={'placeholder': 'Enter 13-digit ISBN'}))

    def clean_isbn(self):
        data = self.cleaned_data['isbn']
        if len(data) != 13:
            raise ValidationError("Invalid code - ISBN has to be 13 digits")
        
        if not data.isdigit():
            raise ValidationError("Invalid code - ISBN has to be 13 digits")
        
        return data

    def is_valid_isbn13(self, isbn):
        """
        Validate the ISBN-13 checksum.
        """
        total = 0
        for i, char in enumerate(isbn[:12]):
            digit = int(char)
            if i % 2 == 0:
                total += digit
            else:
                total += digit * 3
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(isbn[-1])


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

    def is_valid_isbn13(self, isbn):
        """
        Validate the ISBN-13 checksum.
        """
        total = 0
        for i, char in enumerate(isbn[:12]):
            digit = int(char)
            if i % 2 == 0:
                total += digit
            else:
                total += digit * 3
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(isbn[-1])
    
    
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
            existing_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in existing_classes:
                # Append form-control without overwriting
                field.widget.attrs['class'] = (existing_classes + ' form-control').strip()
    
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
    
    def clean_publish_date(self):
        data = self.cleaned_data.get('publish_date', '')
        validate_publish_date(data)
        return data

    

class BookConfirmationForm(forms.Form):
    isbn = forms.CharField(max_length=13, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255, required=False)
    publish_date = forms.CharField(max_length=15, required=False)
    subject = forms.CharField(widget=forms.Textarea, required=False)
    image_url = forms.URLField(required=False)
    storage_name = forms.CharField(max_length=255)  

    def clean_publish_date(self):
        data = self.cleaned_data.get('publish_date', '')
        validate_publish_date(data)
        return data
