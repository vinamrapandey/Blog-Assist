from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.models import Config, Log, PostRecord, User
from backend.core.scheduler import start_agent, stop_agent, get_job_status, log_message
from backend.services.tasks import run_generation_cycle
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from backend.api.auth import get_current_user

router = APIRouter()

class ConfigSchema(BaseModel):
    llm_provider: str
    api_key: str
    wp_url: str
    wp_user: str
    wp_password: str
    topic: str
    word_count: int
    schedule_interval: int
    post_status: str
    google_analytics_id: str

@router.get("/config")
def get_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    if not config:
        config = Config(user_id=current_user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.post("/config")
def update_config(config_data: ConfigSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    if not config:
        config = Config(user_id=current_user.id)
        db.add(config)
    
    for key, value in config_data.dict().items():
        setattr(config, key, value)
    
    db.commit()
    return {"status": "success", "message": "Configuration saved"}

@router.post("/start")
def start_agent_api(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    if not config or not config.wp_url or not config.wp_user or not config.wp_password:
        raise HTTPException(status_code=400, detail="Incomplete configuration. Please save WP credentials.")
    if config.llm_provider != "Simulated" and not config.api_key:
        raise HTTPException(status_code=400, detail="API Key required for real models.")

    def job_wrapper():
        run_generation_cycle(
            provider=config.llm_provider,
            key=config.api_key,
            topic=config.topic,
            count=config.word_count,
            url=config.wp_url,
            user=config.wp_user,
            password=config.wp_password,
            status=config.post_status,
            user_id=current_user.id
        )

    # Note: APScheduler in a multi-tenant environment is complex. 
    # For now, we namespace the job by user_id to prevent conflicts.
    start_agent(config.schedule_interval, job_wrapper, job_id=f"auto_post_{current_user.id}")
    config.is_agent_running = True
    db.commit()
    return {"status": "success", "message": "Agent started"}

@router.post("/stop")
def stop_agent_api(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stop_agent(job_id=f"auto_post_{current_user.id}")
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    if config:
        config.is_agent_running = False
        db.commit()
    return {"status": "success", "message": "Agent stopped"}

@router.post("/run-manual")
def run_manual(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    if not config or not config.wp_url or not config.wp_user or not config.wp_password:
        raise HTTPException(status_code=400, detail="Incomplete configuration.")
    if config.llm_provider != "Simulated" and not config.api_key:
        raise HTTPException(status_code=400, detail="API Key required for real models.")

    log_message("Starting manual run...", user_id=current_user.id)
    run_generation_cycle(
            provider=config.llm_provider,
            key=config.api_key,
            topic=config.topic,
            count=config.word_count,
            url=config.wp_url,
            user=config.wp_user,
            password=config.wp_password,
            status=config.post_status,
            user_id=current_user.id
        )
    return {"status": "success", "message": "Manual run completed"}

@router.get("/status")
def get_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_job_status(job_id=f"auto_post_{current_user.id}")

@router.get("/logs")
def get_logs(limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logs = db.query(Log).filter(Log.user_id == current_user.id).order_by(Log.timestamp.desc()).limit(limit).all()
    return [f"[{log.timestamp.strftime('%H:%M:%S')}] {log.message}" for log in reversed(logs)]

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_posts = db.query(PostRecord).filter(PostRecord.user_id == current_user.id).count()
    today = datetime.utcnow().date()
    days = []
    counts = []
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        start_of_day = datetime(target_date.year, target_date.month, target_date.day)
        end_of_day = start_of_day + timedelta(days=1)
        
        count = db.query(PostRecord).filter(
            PostRecord.user_id == current_user.id,
            PostRecord.timestamp >= start_of_day,
            PostRecord.timestamp < end_of_day
        ).count()
        
        days.append(target_date.strftime("%a"))
        counts.append(count)
        
    return {
        "total_posts": total_posts,
        "labels": days,
        "data": counts
    }
