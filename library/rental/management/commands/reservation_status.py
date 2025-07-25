from django.core.management.base import BaseCommand
from django.utils import timezone
from rental.models import Reservation, Loan

class Command(BaseCommand):
    help = 'Show reservation queue status'

    def handle(self, *args, **options):
        today = timezone.localdate()
        
        # Find reservations that should have started but are waiting
        waiting_reservations = Reservation.objects.filter(future_rent__lte=today)
        
        self.stdout.write(f"=== RESERVATION QUEUE STATUS ({today}) ===\n")
        
        if not waiting_reservations.exists():
            self.stdout.write(self.style.SUCCESS("No reservations waiting - all processed!"))
            return
        
        ready_count = 0
        waiting_count = 0
        
        for res in waiting_reservations:
            # Check if book is available
            current_loan = Loan.objects.filter(
                book_instance=res.book_instance,
                return_date__isnull=True
            ).first()
            
            if current_loan:
                # Book is on loan - reservation is waiting
                days_overdue = (today - current_loan.due_date).days if current_loan.due_date < today else 0
                status = "OVERDUE" if days_overdue > 0 else "ON LOAN"
                
                self.stdout.write(f"WAITING - Reservation {res.reserve_id}")
                self.stdout.write(f"User: {res.employee.username}")
                self.stdout.write(f"Book: {res.book_instance.book.title}")
                self.stdout.write(f"Should have started: {res.future_rent}")
                self.stdout.write(f"Status: {status}")
                if days_overdue > 0:
                    self.stdout.write(f"   Overdue by: {days_overdue} days")
                self.stdout.write(f"   Current borrower: {current_loan.employee.username}")
                self.stdout.write("")
                waiting_count += 1
            else:
                # Book is available - should be processed
                self.stdout.write(f"READY - Reservation {res.reserve_id}")
                self.stdout.write(f"User: {res.employee.username}")
                self.stdout.write(f"Book: {res.book_instance.book.title}")
                self.stdout.write(f"Can be converted now")
                self.stdout.write("")
                ready_count += 1
        
        self.stdout.write(f"SUMMARY:")
        self.stdout.write(f"Ready for conversion: {ready_count}")
        self.stdout.write(f"Waiting for book return: {waiting_count}")
        
        if ready_count > 0:
            self.stdout.write(f"\nRun 'python manage.py convert_reservations' to process ready reservations")
