# forms.py
from django import forms

# In your BookInstanceSearchForm
class BookInstanceSearchForm(forms.Form):
    isbn = forms.CharField(
        label='ISBN', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    title = forms.CharField(
        label='Title', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    author = forms.CharField(
        label='Author', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
