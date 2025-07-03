from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import EmployeeCreationForm, LibrarianCreationForm, CustomAuthenticationForm, EmployeeLoginForm, LibrarianLoginForm

def employee_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user and user.user_type == 'employee':
                login(request, user)
                return redirect('rental:rental_index')  # Redirect to rental app
            else:
                messages.error(request, 'Invalid credentials or not an employee account')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/employee_login.html', {'form': form})

def librarian_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user and user.user_type == 'librarian':
                login(request, user)
                return redirect('registration_book:index')  # Redirect to registration app
            else:
                messages.error(request, 'Invalid credentials or not a librarian account')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/librarian_login.html', {'form': form})

def register_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Employee account created successfully!')
            return redirect('accounts:employee_login')
    else:
        form = EmployeeCreationForm()
    
    return render(request, 'accounts/register_employee.html', {'form': form})

def register_librarian(request):
    if request.method == 'POST':
        form = LibrarianCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Librarian account created successfully!')
            return redirect('accounts:librarian_login')
    else:
        form = LibrarianCreationForm()
    
    return render(request, 'accounts/register_librarian.html', {'form': form})


# class EmployeeLoginView(LoginView):
#     template_name = 'accounts/employee_login.html'
#     authentication_form = EmployeeLoginForm  # as defined earlier
#     redirect_authenticated_user = True
#     next_page = reverse_lazy('rental:rental_index')


# class LibrarianLoginView(LoginView):
#     template_name = 'accounts/librarian_login.html'
#     authentication_form = LibrarianLoginForm  # as defined earlier
#     redirect_authenticated_user = True
#     next_page = reverse_lazy('registration_book:index')
    

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('accounts:login_choice')

def login_choice(request):
    return render(request, 'accounts/login_choice.html')

@login_required
def profile_redirect(request):
    """After login, send user to their correct app home."""
    user = request.user
    if user.user_type == 'employee':
        return redirect('rental_index')
    if user.user_type == 'librarian':
        return redirect('reg_index')
    # Fallback for true admins
    return redirect('admin/')