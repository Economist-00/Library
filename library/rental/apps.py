from django.apps import AppConfig
import sys


class RentalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rental'


class RentalConfig(AppConfig):
    name = 'rental'
    def ready(self):
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            from .apscheduler import start_scheduler
            start_scheduler()