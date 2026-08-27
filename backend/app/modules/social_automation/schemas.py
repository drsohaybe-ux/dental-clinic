from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from .models import PostStatus

class SocialPostBase(BaseModel):
    title: str
    platform: str = "instagram"
    caption: str
    hashtags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    status: PostStatus = PostStatus.WAITING_APPROVAL
    scheduled_for: Optional[str] = None
    ai_notes: Optional[str] = None
    feedback: Optional[str] = None
    approval_webhook_url: Optional[str] = None

class SocialPostCreate(SocialPostBase):
    id: str

class SocialPostUpdate(BaseModel):
    status: Optional[PostStatus] = None
    caption: Optional[str] = None
    feedback: Optional[str] = None

class SocialPostResponse(SocialPostBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# n8n incoming webhook schema
class N8nIncomingDraft(BaseModel):
    event: Optional[str] = None
    postId: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    caption: Optional[str] = None
    mediaUrl: Optional[str] = None
    imageUrl: Optional[str] = None
    hashtags: Optional[List[str]] = None
    platform: Optional[str] = None
    platform_posts: Optional[Any] = None
    status: Optional[str] = None
    approvalWebhookUrl: Optional[str] = None
    scheduledFor: Optional[str] = None
    aiNotes: Optional[str] = None
