from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.models import Config, Log
from backend.core.scheduler import start_agent, stop_agent, get_job_status, log_message
from backend.services.tasks import run_generation_cycle
from pydantic import BaseModel
from typing import List

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

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    config = db.query(Config).first()
    if not config:
        config = Config()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.post("/config")
def update_config(config_data: ConfigSchema, db: Session = Depends(get_db)):
    config = db.query(Config).first()
    if not config:
        config = Config()
        db.add(config)
    
    for key, value in config_data.dict().items():
        setattr(config, key, value)
    
    db.commit()
    return {"status": "success", "message": "Configuration saved"}

@router.post("/start")
def start_agent_api(db: Session = Depends(get_db)):
    config = db.query(Config).first()
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
            status=config.post_status
        )

    start_agent(config.schedule_interval, job_wrapper)
    config.is_agent_running = True
    db.commit()
    return {"status": "success", "message": "Agent started"}

@router.post("/stop")
def stop_agent_api(db: Session = Depends(get_db)):
    stop_agent()
    config = db.query(Config).first()
    if config:
        config.is_agent_running = False
        db.commit()
    return {"status": "success", "message": "Agent stopped"}

@router.post("/run-manual")
def run_manual(db: Session = Depends(get_db)):
    config = db.query(Config).first()
    if not config or not config.wp_url or not config.wp_user or not config.wp_password:
        raise HTTPException(status_code=400, detail="Incomplete configuration.")
    if config.llm_provider != "Simulated" and not config.api_key:
        raise HTTPException(status_code=400, detail="API Key required for real models.")

    log_message("Starting manual run...")
    # Fire off immediately in background, or just run it synchronously. We'll run it synchronously for simplicity in manual run.
    run_generation_cycle(
            provider=config.llm_provider,
            key=config.api_key,
            topic=config.topic,
            count=config.word_count,
            url=config.wp_url,
            user=config.wp_user,
            password=config.wp_password,
            status=config.post_status
        )
    return {"status": "success", "message": "Manual run completed"}

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    return get_job_status()

@router.get("/logs")
def get_logs(limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(limit).all()
    # Return formatted strings to match old UI
    return [f"[{log.timestamp.strftime('%H:%M:%S')}] {log.message}" for log in reversed(logs)]
