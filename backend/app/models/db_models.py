from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    token_version = Column(Integer, default=0, nullable=False)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    histories = relationship("DetectionHistory", back_populates="user", cascade="all, delete-orphan")


class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    media_type = Column(String(10), default="image", nullable=False)  # image / video
    original_image = Column(String(500))
    result_image = Column(String(500))
    video_url = Column(String(500))
    result_video_url = Column(String(500))
    frame_count = Column(Integer)
    fps = Column(Float)
    duration = Column(Float)
    model_name = Column(String(50))
    total_objects = Column(Integer, default=0)
    detection_time = Column(Float)
    boxes = Column(JSON)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("User", back_populates="histories")


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)
    revoked_at = Column(DateTime, default=_utcnow)


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(5000), nullable=False)
    image_url = Column(String(500))
    status = Column(String(20), default="pending", nullable=False)  # pending / approved / rejected
    is_pinned = Column(Boolean, default=False, nullable=False)
    admin_note = Column(String(500))
    created_at = Column(DateTime, default=_utcnow, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")
    comments = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan")


class ForumComment(Base):
    __tablename__ = "forum_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    post = relationship("ForumPost", back_populates="comments")
    user = relationship("User")
