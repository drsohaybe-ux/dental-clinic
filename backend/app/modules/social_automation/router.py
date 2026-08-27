import os
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.auth.dependencies import get_clinic_context, ClinicContext
from .models import SocialPost, PostStatus
from .schemas import SocialPostResponse, SocialPostUpdate, N8nIncomingDraft

router = APIRouter(tags=["social_automation"])

@router.post("/webhook/incoming", response_model=SocialPostResponse, summary="Receive draft from n8n")
async def receive_n8n_draft(
    payload: N8nIncomingDraft,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Receives an incoming draft from the n8n webhook. 
    Protected by DENTALPIN_N8N_SECRET to prevent unauthorized spam.
    """
    expected_secret = os.environ.get("DENTALPIN_N8N_SECRET")
    
    if expected_secret:
        # Check standard Authorization Bearer or custom header format
        token = authorization.replace("Bearer ", "") if authorization else None
        if token != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing n8n webhook secret"
            )

    # Normalize the incoming payload
    instagram_data = payload.platform_posts.get("Instagram", {}) if isinstance(payload.platform_posts, dict) else {}
    facebook_data = payload.platform_posts.get("Facebook", {}) if isinstance(payload.platform_posts, dict) else {}
    
    # Resolve caption safely
    caption = payload.caption
    if not caption:
        if instagram_data.get("caption"):
            cta = instagram_data.get("call_to_action", "")
            caption = f"{instagram_data['caption']}\n\n{cta}" if cta else instagram_data["caption"]
        elif facebook_data.get("post"):
            cta = facebook_data.get("call_to_action", "")
            caption = f"{facebook_data['post']}\n\n{cta}" if cta else facebook_data["post"]
        elif payload.description:
            caption = payload.description
        else:
            caption = "Nouvelle publication préparée."

    # Resolve hashtags safely
    hashtags = payload.hashtags
    if not hashtags or not isinstance(hashtags, list):
        hashtags = instagram_data.get("hashtags") or facebook_data.get("hashtags") or []

    # Finalize fields
    image_url = payload.imageUrl or payload.mediaUrl or ""
    title = payload.title or "Publication Cabinet Dentaire"
    platform = payload.platform or ("instagram" if instagram_data else "facebook")
    post_id = payload.postId or f"post-{int(datetime.utcnow().timestamp())}"

    new_post = SocialPost(
        id=post_id,
        platform=platform,
        title=title,
        caption=caption.strip(),
        hashtags=hashtags,
        image_url=image_url,
        status=PostStatus.WAITING_APPROVAL,
        scheduled_for=payload.scheduledFor or "Demain à 10h00",
        ai_notes=payload.aiNotes or "Généré automatiquement par Dr. Mokhtar AI (n8n).",
        approval_webhook_url=payload.approvalWebhookUrl,
    )
    
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    return new_post

@router.get("/posts", response_model=list[SocialPostResponse], summary="List all social posts")
async def get_social_posts(
    context: ClinicContext = Depends(get_clinic_context),
    db: AsyncSession = Depends(get_db)
):
    """
    List all social posts for the dashboard. Protected by standard auth.
    """
    # Assuming standard sorting: newest first
    stmt = select(SocialPost).order_by(SocialPost.created_at.desc())
    result = await db.execute(stmt)
    posts = result.scalars().all()
    return posts

@router.patch("/posts/{post_id}", response_model=SocialPostResponse, summary="Update social post")
async def update_social_post(
    post_id: str,
    update_data: SocialPostUpdate,
    context: ClinicContext = Depends(get_clinic_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Update post status or text.
    """
    stmt = select(SocialPost).where(SocialPost.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Social post not found")
        
    if update_data.status:
        post.status = update_data.status
    if update_data.caption is not None:
        post.caption = update_data.caption
    if update_data.feedback is not None:
        post.feedback = update_data.feedback
        
    await db.commit()
    await db.refresh(post)
    return post
