import schedule
import time
import threading
import datetime

class AgentScheduler:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.job = None
        self.next_run_time = None
        self.last_run_time = None
        self.last_run_status = "Not started"

    def start(self, interval_hours, job_function):
        if self.is_running:
            return
        
        self.is_running = True
        schedule.clear()
        
        # Schedule the job
        # For testing, we might want minutes, but for prod use hours
        self.job = schedule.every(interval_hours).hours.do(job_function)
        
        self.next_run_time = self.job.next_run
        
        self.thread = threading.Thread(target=self._run_continuously)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.is_running = False
        schedule.clear()
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

    def _run_continuously(self):
        while self.is_running:
            schedule.run_pending()
            if self.job:
                self.next_run_time = self.job.next_run
            time.sleep(1)

    def get_status(self):
        return {
            "is_running": self.is_running,
            "next_run": self.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if self.next_run_time else "N/A",
            "last_run": self.last_run_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_run_time else "N/A",
            "status_msg": self.last_run_status
        }

    def update_last_run(self, status):
        self.last_run_time = datetime.datetime.now()
        self.last_run_status = status
