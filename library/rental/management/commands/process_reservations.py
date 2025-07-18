from django.core.management.base import BaseCommand
from rental.apscheduler import process_reservations

class Command(BaseCommand):
    help = 'Manually process today\'s reservations'

    def handle(self, *args, **options):
        processed, errors = process_reservations()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully processed {processed} reservations with {errors} errors')
        )