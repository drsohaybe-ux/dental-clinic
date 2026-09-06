from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, Text, JSON, Enum, UniqueConstraint, Index
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

class SocialMediaInsight(Base):
    __tablename__ = "social_media_insights"
    __table_args__ = (
        UniqueConstraint("platform", "account_id", "date", name="uq_social_insights_platform_account_date"),
        Index("idx_social_media_insights_platform_date", "platform", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # 'instagram' or 'facebook'
    account_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_followers: Mapped[int] = mapped_column(nullable=False, default=0)
    reach: Mapped[int] = mapped_column(nullable=False, default=0)
    profile_views: Mapped[int] = mapped_column(nullable=False, default=0)
    website_clicks: Mapped[int] = mapped_column(nullable=False, default=0)
    saves: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


