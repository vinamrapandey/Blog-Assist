from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from backend.core.database import Base

class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, index=True)
    llm_provider = Column(String, default="Google Gemini")
    api_key = Column(String, default="")
    wp_url = Column(String, default="")
    wp_user = Column(String, default="")
    wp_password = Column(String, default="")
    topic = Column(String, default="Tech")
    word_count = Column(Integer, default=500)
    schedule_interval = Column(Integer, default=24)
    post_status = Column(String, default="draft")
    is_agent_running = Column(Boolean, default=False)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(String)
