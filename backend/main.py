from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router as api_router
from backend.api.auth import router as auth_router
from backend.core.database import engine, Base, SessionLocal
from backend.models.models import Config
from backend.core.scheduler import start_agent
from backend.services.tasks import run_generation_cycle
import os

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blog Assist API")

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        configs = db.query(Config).filter(Config.is_agent_running == True).all()
        for config in configs:
            if config.wp_url and config.wp_user and config.wp_password:
                provider = config.llm_provider
                key = config.api_key
                topic = config.topic
                count = config.word_count
                url = config.wp_url
                user = config.wp_user
                password = config.wp_password
                status = config.post_status
                user_id = config.user_id
                schedule_interval = config.schedule_interval
                
                # Use default args to bind variables locally per iteration
                def job_wrapper(p=provider, k=key, t=topic, c=count, u=url, usr=user, pwd=password, s=status, uid=user_id):
                    run_generation_cycle(
                        provider=p, key=k, topic=t, count=c, url=u, user=usr, password=pwd, status=s, user_id=uid
                    )
                
                start_agent(schedule_interval, job_wrapper, job_id=f"auto_post_{user_id}")
    finally:
        db.close()

# Setup CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(auth_router, prefix="/api/auth")
app.include_router(api_router, prefix="/api")

# Serve static frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "public")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
