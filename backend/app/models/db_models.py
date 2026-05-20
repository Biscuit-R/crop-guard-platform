from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    histories = relationship("DetectionHistory", back_populates="user")


class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_image = Column(String(500))
    result_image = Column(String(500))
    model_name = Column(String(50))
    total_objects = Column(Integer, default=0)
    detection_time = Column(Float)
    boxes = Column(JSON)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="histories")
