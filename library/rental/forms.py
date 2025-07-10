# forms.py
from django import forms
from datetime import date, timedelta


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


class DeleteAccountForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        # Check that the entered username matches the logged-in user
        if username != self.user.username:
            raise forms.ValidationError("The username does not match your account.")

        # Verify the password against the user's actual password hash
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password. Please try again.")
        return cleaned_data


class RentForm(forms.Form):
    due_date = forms.DateField(
        label='Due Date',
        widget=forms.DateInput(attrs={
            'type': 'date',
            # set min = today, max = today +14 days
            'min': date.today().isoformat(),
            'max': (date.today() + timedelta(weeks=2)).isoformat(),
            'class': 'form-control'
        })
    )

    def clean_due_date(self):
        d = self.cleaned_data['due_date']
        today = date.today()
        if d < today:
            raise forms.ValidationError("Due date cannot be in the past.")
        if d > today + timedelta(weeks=2):
            raise forms.ValidationError("Due date must be within two weeks.")
        return d