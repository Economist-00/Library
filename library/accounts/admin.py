from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Employee, Librarian

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'user_type', 'is_active', 'is_staff')
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('username',)
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'user_type', 'password1', 'password2'),
        }),
    )

@admin.register(CustomUser)
class UserAdmin(CustomUserAdmin):
    pass

@admin.register(Employee)
class EmployeeAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='employee')

@admin.register(Librarian)
class LibrarianAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='librarian')
