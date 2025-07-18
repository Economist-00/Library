import logging
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.utils import timezone
from .models import Reservation, Loan

logger = logging.getLogger(__name__)

def process_reservations():
    """Convert today's reservations into loans."""
    today = timezone.localdate()
    logger.info(f"Processing reservations for {today}")
    
    reservations_to_process = Reservation.objects.filter(future_rent=today)
    logger.info(f"Found {reservations_to_process.count()} reservations to process")
    
    processed_count = 0
    error_count = 0
    
    for res in reservations_to_process:
        try:
            # Check if book instance is available
            existing_loan = Loan.objects.filter(
                book_instance=res.book_instance,
                return_date__isnull=True
            ).first()
            
            if existing_loan:
                logger.warning(f"Skipping reservation {res.reserve_id} - book instance already on loan")
                continue
            
            # Create loan
            loan = Loan.objects.create(
                book_instance=res.book_instance,
                employee=res.employee,
                loan_start=res.future_rent,
                due_date=res.future_return,
            )
            
            # Delete reservation
            res.delete()
            
            processed_count += 1
            logger.info(f"Converted reservation {res.reserve_id} to loan {loan.loan_id}")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing reservation {res.reserve_id}: {str(e)}")
    
    logger.info(f"Processing complete. Converted: {processed_count}, Errors: {error_count}")
    return processed_count, error_count

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Add the job
    scheduler.add_job(
        process_reservations,
        'cron',
        hour=0, minute=0,
        name="Process today's reservations",
        id="process_reservations"  # Add unique ID
    )
    
    register_events(scheduler)
    scheduler.start()
    logger.info("Scheduler started successfully")
