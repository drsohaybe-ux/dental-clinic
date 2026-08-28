from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum

class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"

class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    platform: Mapped[str] = mapped_column(String, nullable=False, default="instagram")
    title: Mapped[str] = mapped_column(String, nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus), nullable=False, default=PostStatus.WAITING_APPROVAL)
    scheduled_for: Mapped[str] = mapped_column(String, nullable=True)
    ai_notes: Mapped[str] = mapped_column(Text, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    approval_webhook_url: Mapped[str] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
