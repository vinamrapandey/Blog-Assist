from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
from sqlalchemy.orm import Session
from backend.core.database import SessionLocal
from backend.models.models import Log

scheduler = BackgroundScheduler()

def log_message(message: str, user_id: int = None):
    db = SessionLocal()
    try:
        new_log = Log(message=message, user_id=user_id)
        db.add(new_log)
        db.commit()
    finally:
        db.close()
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User {user_id}: {message}")

def get_job_status(job_id: str = 'blog_job'):
    job = scheduler.get_job(job_id)
    if job:
        return {
            "is_running": True,
            "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
        }
    return {"is_running": False, "next_run": "N/A"}

def start_agent(interval_minutes: int, job_function, job_id: str = 'blog_job'):
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        
    scheduler.add_job(
        func=job_function,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=job_id,
        name='Generate and publish blog post',
        replace_existing=True,
        next_run_time=datetime.datetime.now()
    )
    if not scheduler.running:
        scheduler.start()
    
    # We extract user_id from job_id if we used the convention auto_post_{user_id}
    try:
        user_id = int(job_id.split('_')[-1])
        log_message(f"Agent started. Running every {interval_minutes} minutes.", user_id=user_id)
    except:
        log_message(f"Agent started. Running every {interval_minutes} minutes.")

def stop_agent(job_id: str = 'blog_job'):
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    try:
        user_id = int(job_id.split('_')[-1])
        log_message("Agent stopped.", user_id=user_id)
    except:
        log_message("Agent stopped.")
