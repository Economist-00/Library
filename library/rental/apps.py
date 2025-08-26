from django.apps import AppConfig
import os
import threading
import time



class RentalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rental'

    def ready(self):
        # Only in main process
        if os.environ.get('RUN_MAIN') == 'true':
            # Small delay to avoid database warnings
            def start_scheduler():
                time.sleep(1)
                try:
                    from . import apscheduler
                    apscheduler.start()
                except Exception as e:
                    print(f"Scheduler start error: {e}")
            
            thread = threading.Thread(target=start_scheduler)
            thread.daemon = True
            thread.start()

