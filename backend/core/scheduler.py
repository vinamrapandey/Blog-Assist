from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models.models import Log

scheduler = BackgroundScheduler()

def log_message(message: str):
    db = SessionLocal()
    try:
        new_log = Log(message=message)
        db.add(new_log)
        db.commit()
    finally:
        db.close()
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_job_status():
    job = scheduler.get_job('blog_job')
    if job:
        return {
            "is_running": True,
            "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
        }
    return {"is_running": False, "next_run": "N/A"}

def start_agent(interval_hours: int, job_function):
    if scheduler.get_job('blog_job'):
        scheduler.remove_job('blog_job')
        
    scheduler.add_job(
        func=job_function,
        trigger=IntervalTrigger(hours=interval_hours),
        id='blog_job',
        name='Generate and publish blog post',
        replace_existing=True
    )
    if not scheduler.running:
        scheduler.start()
    log_message(f"Agent started. Running every {interval_hours} hours.")

def stop_agent():
    if scheduler.get_job('blog_job'):
        scheduler.remove_job('blog_job')
    log_message("Agent stopped.")
