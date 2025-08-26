from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .forms import EmployeeCreationForm, CustomAuthenticationForm

def employee_login(request):
    if request.user.is_authenticated:
        return redirect('rental_index')
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user and user.user_type == 'employee':
                login(request, user)
                return redirect('rental_index')
            else:
                messages.error(request, 'Invalid credentials or not an employee account')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/employee_login.html', {'form': form})

def librarian_login(request):
    if request.user.is_authenticated:
        return redirect('reg_index')
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user and user.user_type == 'librarian':
                login(request, user)
                return redirect('reg_index')
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
            return redirect('employee_login')
    else:
        form = EmployeeCreationForm()
    
    return render(request, 'accounts/register_employee.html', {'form': form})

    


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('login_choice')

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