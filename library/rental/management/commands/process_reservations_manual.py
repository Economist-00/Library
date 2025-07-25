from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from rental.models import Reservation, Loan

class Command(BaseCommand):
    help = 'Manually process reservations for today and convert them to loans'

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(f"Processing reservations for date: {today}")
        
        with transaction.atomic():
            reservations = Reservation.objects.select_for_update().filter(
                start_date__lte=today,
                status=Reservation.Status.RESERVED
            )
            
            processed_count = 0
            for reservation in reservations:
                loan = Loan.objects.create(
                    instance=reservation.instance,
                    borrower=reservation.user,
                    start_date=today,
                    due_date=reservation.expected_return,
                )
                
                reservation.status = Reservation.Status.CONVERTED
                reservation.save(update_fields=["status"])
                
                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Converted reservation {reservation.id} to loan {loan.id}"
                    )
                )
            
            self.stdout.write(f"Processed {processed_count} reservations")
