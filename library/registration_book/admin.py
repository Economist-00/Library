from django.contrib import admin

# Register your models here.
from .models import Storage, BookInstance, Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # Display these fields in the list view of all storages
    list_display = ('title', 'author')
    # Add a search bar to search by these fields
    search_fields = ('title',)

@admin.register(BookInstance)
class CollectionAdmin(admin.ModelAdmin):
    # You can even display fields from related models
    list_display = ('book_instance_id', 'storage')
    # Make the 'storage' field a searchable dropdown instead of a simple text input
    raw_id_fields = ('storage',)

admin.site.register(Storage)