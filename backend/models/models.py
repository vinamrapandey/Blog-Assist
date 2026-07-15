from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    configs = relationship("Config", back_populates="owner")
    logs = relationship("Log", back_populates="owner")
    posts = relationship("PostRecord", back_populates="owner")
    guidelines = relationship("StyleGuidelines", back_populates="owner")

class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    llm_provider = Column(String, default="Google Gemini")
    api_key = Column(String, default="")
    wp_url = Column(String, default="")
    wp_user = Column(String, default="")
    wp_password = Column(String, default="")
    topic = Column(String, default="Tech")
    word_count = Column(Integer, default=500)
    schedule_interval = Column(Integer, default=1440)
    post_status = Column(String, default="draft")
    is_agent_running = Column(Boolean, default=False)
    google_analytics_id = Column(String, default="")
    
    owner = relationship("User", back_populates="configs")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(String)

    owner = relationship("User", back_populates="logs")

class PostRecord(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    title = Column(String)
    topic = Column(String)
    status = Column(String)
    
    owner = relationship("User", back_populates="posts")

class StyleGuidelines(Base):
    __tablename__ = "style_guidelines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    rule = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="guidelines")
