from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from rental.models import Reservation, Loan

class Command(BaseCommand):
    help = 'Convert overdue reservations to loans'

    def handle(self, *args, **options):
        today = timezone.localdate()
        self.stdout.write(f"Today: {today}")
        
        # Find reservations to convert
        overdue = Reservation.objects.filter(
            future_rent__lte=today,
            future_rent__isnull=False
        )
        
        self.stdout.write(f"Found {overdue.count()} reservations to convert")
        
        if not overdue.exists():
            self.stdout.write(self.style.WARNING("No reservations need converting"))
            return
        
        converted = 0
        for res in overdue:
            self.stdout.write(f"\nProcessing Reservation {res.reserve_id}:")
            self.stdout.write(f"User: {res.employee.username}")
            self.stdout.write(f"Book: {res.book_instance.book.title}")
            self.stdout.write(f"Start: {res.future_rent}")
            
            try:
                # Check existing loan
                if Loan.objects.filter(book_instance=res.book_instance, employee=res.employee).exists():
                    self.stdout.write(self.style.WARNING("Already has loan - marking processed"))
                    res.future_rent = None
                    res.save()
                    continue
                
                # Create loan
                with transaction.atomic():
                    loan = Loan.objects.create(
                        book_instance=res.book_instance,
                        employee=res.employee,
                        loan_start=today,
                        due_date=res.future_return,
                    )
                    
                    res.future_rent = None
                    res.save()
                    
                    converted += 1
                    self.stdout.write(self.style.SUCCESS(f"Created loan {loan.loan_id}"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nCONVERTED: {converted} reservations"))
