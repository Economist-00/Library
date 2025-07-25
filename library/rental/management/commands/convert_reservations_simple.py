from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from rental.models import Reservation, Loan

class Command(BaseCommand):
    help = 'Convert reservations to loans and delete reservations'

    def handle(self, *args, **options):
        today = timezone.localdate()
        
        # Simple query - just get all overdue reservations
        overdue = Reservation.objects.filter(future_rent__lte=today)
        
        self.stdout.write(f"Found {overdue.count()} reservations to convert")
        
        converted = 0
        for res in overdue:
            try:
                with transaction.atomic():
                    # Check for existing loan
                    if Loan.objects.filter(book_instance=res.book_instance, employee=res.employee).exists():
                        self.stdout.write(f"Loan exists - deleting duplicate reservation {res.reserve_id}")
                        res.delete()
                        continue
                    
                    # Create loan and delete reservation
                    loan = Loan.objects.create(
                        book_instance=res.book_instance,
                        employee=res.employee,
                        loan_start=today,
                        due_date=res.future_return,
                    )
                    
                    res.delete()  
                    
                    converted += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Converted reservation → loan {loan.loan_id} (deleted reservation)")
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error: {e}")
                )
        
        self.stdout.write(self.style.SUCCESS(f"Converted {converted} reservations"))
