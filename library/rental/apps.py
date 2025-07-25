from django.apps import AppConfig
import os

class RentalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rental'

    def ready(self):
        # Only in main process
        if os.environ.get('RUN_MAIN') == 'true':
            # Small delay to avoid database warnings
            import threading
            import time
            
            def start_scheduler():
                time.sleep(1)  # Wait 1 second
                try:
                    from . import apscheduler
                    apscheduler.start()
                except Exception as e:
                    print(f"Scheduler start error: {e}")
            
            thread = threading.Thread(target=start_scheduler)
            thread.daemon = True
            thread.start()

