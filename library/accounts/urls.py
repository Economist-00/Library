from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import EmployeeLoginForm, LibrarianLoginForm
from . import views
# from .views import EmployeeLoginView, LibrarianLoginView

urlpatterns = [
    path('', views.login_choice, name='login_choice'),
    # Employee login
    path(
        'employee/login/',
        auth_views.LoginView.as_view(
            template_name='accounts/employee_login.html',
            authentication_form=EmployeeLoginForm
        ),
        name='employee_login'
    ),

    # Librarian login
    path(
        'librarian/login/',
        auth_views.LoginView.as_view(
            template_name='accounts/librarian_login.html',
            authentication_form=LibrarianLoginForm
        ),
        name='librarian_login'
    ),
    path('profile/', views.profile_redirect, name='profile'),
    path('employee/register/', views.register_employee, name='register_employee'),
    path('logout/', views.user_logout, name='logout'),
]
