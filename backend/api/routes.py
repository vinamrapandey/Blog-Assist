from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.models import Config, Log, PostRecord, User, StyleGuidelines
from backend.core.scheduler import start_agent, stop_agent, get_job_status, log_message
from backend.services.tasks import run_generation_cycle
from backend.services.llm_manager import LLMHandler
from backend.services.wordpress_manager import WordPressHandler
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

    log_message("Generating manual draft for preview...", user_id=current_user.id)
    
    # Fetch guidelines
    guidelines = [g.rule for g in db.query(StyleGuidelines).filter(StyleGuidelines.user_id == current_user.id).all()]
    
    llm = LLMHandler(config.llm_provider, config.api_key)
    result = llm.generate_post(config.topic, config.word_count, guidelines=guidelines)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return {"status": "success", "title": result.get("title", "Draft"), "content": result.get("content", "")}

class FeedbackSchema(BaseModel):
    title: str
    content: str
    feedback: str

@router.post("/submit-feedback")
def submit_feedback(data: FeedbackSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    llm = LLMHandler(config.llm_provider, config.api_key)
    
    existing_guidelines = [g.rule for g in db.query(StyleGuidelines).filter(StyleGuidelines.user_id == current_user.id).all()]
    
    result = llm.process_feedback_and_rewrite(data.title, data.content, data.feedback, guidelines=existing_guidelines)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    # Save the newly extracted rule
    new_rule = result.get("new_rule")
    if new_rule and new_rule.strip():
        rule_record = StyleGuidelines(user_id=current_user.id, rule=new_rule.strip())
        db.add(rule_record)
        db.commit()
        log_message(f"Learned new rule: {new_rule}", user_id=current_user.id)
        
    return {
        "status": "success",
        "title": result.get("title"),
        "content": result.get("content"),
        "learned_rule": new_rule
    }

class PublishSchema(BaseModel):
    title: str
    content: str

@router.post("/publish-draft")
def publish_draft(data: PublishSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.user_id == current_user.id).first()
    
    wp = WordPressHandler(config.wp_url, config.wp_user, config.wp_password)
    result = wp.create_post(data.title, data.content, config.post_status)
    
    if "id" in result:
        new_post = PostRecord(title=data.title, topic=config.topic, status=result.get('status', config.post_status), user_id=current_user.id)
        db.add(new_post)
        db.commit()
        log_message(f"Manually published post ID: {result['id']}", user_id=current_user.id)
        return {"status": "success", "message": "Published successfully!"}
    else:
        raise HTTPException(status_code=500, detail=str(result))

@router.get("/guidelines")
def get_guidelines(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(StyleGuidelines).filter(StyleGuidelines.user_id == current_user.id).order_by(StyleGuidelines.id.desc()).all()

@router.delete("/guidelines/{rule_id}")
def delete_guideline(rule_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = db.query(StyleGuidelines).filter(StyleGuidelines.id == rule_id, StyleGuidelines.user_id == current_user.id).first()
    if rule:
        db.delete(rule)
        db.commit()
    return {"status": "success"}

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
