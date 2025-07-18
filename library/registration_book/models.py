from django.db import models
from django.urls import reverse
import uuid

class Book(models.Model):
    book_id = models.AutoField('書籍ID', primary_key=True)
    isbn = models.CharField('ISBN', max_length=13, unique=True, blank=True, null=True)
    title = models.CharField('タイトル', max_length=255)
    author = models.CharField('著者', max_length=255)
    publish_date = models.CharField('出版日', max_length=15)  # Added max_length
    image_url = models.URLField('画像用リンク', max_length=255, blank=True, null=True)
    subject = models.TextField('ジャンル', blank=True, null=True)
    class Meta:
        ordering = ['title', '-publish_date']
        unique_together = ('title', 'author')
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.book_id)])

class Storage(models.Model):
    storage_id = models.AutoField('保管場所ID', primary_key=True)
    storage_name = models.CharField('保管場所の名前', max_length=255) 

    def __str__(self):
        return f'{self.storage_name}'
    
class BookInstance(models.Model):
    book_instance_id = models.UUIDField('蔵書ID', primary_key=True, default=uuid.uuid4)
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='instances')

    class Meta:
        ordering = ['book_instance_id']

    def __str__(self):
        return f'{self.book_instance_id} : {self.book.title} in {self.storage.storage_name}'
