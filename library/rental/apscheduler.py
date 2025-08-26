import logging
import os
import sys
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler import util

from .models import Reservation, Loan

# FORCE console logging
class ConsoleHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.setFormatter(formatter)

# Set up logger that WILL show in console
logger = logging.getLogger('apscheduler_rental')
logger.setLevel(logging.INFO)
logger.addHandler(ConsoleHandler())

@util.close_old_connections
def process_reservations():
    """
    Convert reservations to loans only when books are actually available
    """
    today = timezone.localdate()
    logger.info(f"Processing reservations for date {today}")
    
    try:
        # Find reservations that should start today or earlier
        due_reservations = Reservation.objects.filter(future_rent__lte=today)
        
        logger.info(f"Found {due_reservations.count()} reservations due for processing")
        
        if not due_reservations.exists():
            logger.info("No reservations to process")
            return
        
        converted = 0
        waiting = 0
        errors = 0
        
        for res in due_reservations:
            try:
                with transaction.atomic():
                    # Lock the reservation
                    locked_res = Reservation.objects.select_for_update().get(pk=res.pk)
                    
                    duplicate_loan = Loan.objects.filter(
                    book_instance=locked_res.book_instance,
                    employee=locked_res.employee,
                    return_date__isnull=True).first()

                    if duplicate_loan:
                        logger.info(
                            "Employee already has copy on loan "
                            f"(loan {duplicate_loan.loan_id}); deleting duplicate reservation {locked_res.reserve_id}")
                        locked_res.delete()
                        continue

                    # Availability check (anyone else still on loan)
                    current_loan = Loan.objects.filter(
                        book_instance=locked_res.book_instance,
                        return_date__isnull=True).exclude(employee=locked_res.employee).first()

                    if current_loan:
                        days_overdue = (
                            (today - current_loan.due_date).days
                            if current_loan.due_date and current_loan.due_date < today else 0)
                        status = "overdue" if days_overdue > 0 else "on-loan"
                        logger.info(
                            f"Reservation {locked_res.reserve_id} waiting - book {status} "
                            f"(borrower {current_loan.employee.username}, due {current_loan.due_date})")
                        waiting += 1
                        continue
                        
                    # Book is available - convert reservation to loan
                    loan = Loan.objects.create(
                        book_instance=locked_res.book_instance,
                        employee=locked_res.employee,
                        loan_start=today,
                        due_date=locked_res.future_return,
                    )
                    
                    # Delete the reservation since it's now a loan
                    locked_res.delete()
                    
                    converted += 1
                    logger.info(f"Converted reservation {res.reserve_id} → loan {loan.loan_id}")
                    
            except Reservation.DoesNotExist:
                logger.info(f"Reservation {res.reserve_id} already processed")
                continue
            except Exception as e:
                errors += 1
                logger.error(f"Error processing reservation {res.reserve_id}: {e}")
        
        logger.info(f"Processing complete: {converted} converted, {waiting} waiting for book return, {errors} errors")
        
    except Exception as e:
        logger.error(f"Fatal error in process_reservations: {e}")
        raise

def heartbeat():
    """Heartbeat with forced output"""
    msg = f"SCHEDULER ALIVE at {timezone.now()}"
    print(msg)
    logger.info(msg)
    sys.stdout.write(f"{msg}\n")
    sys.stdout.flush()

def start():
    """Start scheduler with forced output"""
    if os.environ.get("RUN_MAIN") != "true":
        msg = "Not in main process - scheduler won't start"
        print(msg)
        logger.warning(msg)
        return
    
    if getattr(settings, "_scheduler_started", False):
        msg = "Scheduler already started"
        print(msg)
        logger.warning(msg)
        return
    
    try:
        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # Heartbeat every minute
        scheduler.add_job(
            heartbeat,
            trigger="interval",
            minutes=1,
            id="heartbeat",
            max_instances=1,
            replace_existing=True,
        )
        
        # Process every 2 minutes for testing
        scheduler.add_job(
            process_reservations,
            trigger="interval",
            minutes=2,
            id="test_promote",
            max_instances=1,
            replace_existing=True,
        )
        
        # Daily at midnight
        scheduler.add_job(
            process_reservations,
            trigger=CronTrigger(hour=0, minute=0, timezone=settings.TIME_ZONE),
            id="promote_reservations",
            max_instances=1,
            replace_existing=True,
        )
        
        scheduler.start()
        settings._scheduler_started = True
        
        start_msg = f"SCHEDULER STARTED in PID {os.getpid()}"
        print(start_msg)
        logger.info(start_msg)
        sys.stdout.write(f"{start_msg}\n")
        sys.stdout.flush()
        
    except Exception as e:
        error_msg = f"Failed to start scheduler: {e}"
        print(error_msg)
        logger.error(error_msg)
        sys.stdout.write(f"{error_msg}\n")
        sys.stdout.flush()

def delete_old_job_executions(max_age=604_800):
    """Delete old APScheduler job executions from the database."""
    from django_apscheduler.models import DjangoJobExecution
    DjangoJobExecution.objects.delete_old_job_executions(max_age)
