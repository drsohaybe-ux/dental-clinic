import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Union
from uuid import uuid4
import logging
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database import get_db
from .models import SocialPost, PostStatus, SocialMediaInsight
from .schemas import (
    SocialPostResponse,
    SocialPostUpdate,
    N8nIncomingDraft,
    SocialInsightResponse,
    SocialInsightCreate,
    SocialInsightsSyncPayload
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["social_automation"])


@router.post("/webhook/incoming", response_model=SocialPostResponse, summary="Receive draft from n8n")
async def receive_n8n_draft(
    payload: N8nIncomingDraft,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Receives an incoming draft from n8n.
    """
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
            caption = "Nouvelle publication préparée par l'IA."

    # Resolve hashtags safely
    hashtags = payload.hashtags
    if not hashtags or not isinstance(hashtags, list):
        hashtags = instagram_data.get("hashtags") or facebook_data.get("hashtags") or []

    # Finalize fields
    image_url = payload.imageUrl or payload.mediaUrl or ""
    title = payload.title or "Publication Cabinet Dentaire"
    platform = payload.platform or ("instagram" if instagram_data else "facebook")
    post_id = str(payload.postId or f"post-{int(datetime.utcnow().timestamp())}")

    # Check if post already exists
    stmt = select(SocialPost).where(SocialPost.id == post_id)
    res = await db.execute(stmt)
    existing_post = res.scalar_one_or_none()

    if existing_post:
        existing_post.title = title
        existing_post.caption = caption.strip()
        existing_post.hashtags = hashtags
        existing_post.image_url = image_url
        existing_post.status = PostStatus.WAITING_APPROVAL
        existing_post.platform = platform
        existing_post.scheduled_for = payload.scheduledFor or existing_post.scheduled_for or "Demain à 10h00"
        existing_post.ai_notes = payload.aiNotes or existing_post.ai_notes
        await db.commit()
        await db.refresh(existing_post)
        return existing_post

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
    db: AsyncSession = Depends(get_db)
):
    """
    List all social posts for the dashboard.
    """
    stmt = select(SocialPost).order_by(SocialPost.created_at.desc())
    result = await db.execute(stmt)
    posts = result.scalars().all()
    return posts

@router.patch("/posts/{post_id}", response_model=SocialPostResponse, summary="Update social post")
async def update_social_post(
    post_id: str,
    update_data: SocialPostUpdate,
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

@router.delete("/posts/{post_id}", summary="Delete social post")
async def delete_social_post(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a social post permanently from the database.
    """
    stmt = select(SocialPost).where(SocialPost.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    
    if post:
        await db.delete(post)
        await db.commit()
        
    return {"success": True, "message": "Social post deleted successfully", "id": post_id}

@router.get("/insights", response_model=list[SocialInsightResponse], summary="Get social media performance insights")
async def get_social_insights(
    platform: Optional[str] = Query(None, description="Filter by platform ('instagram' or 'facebook')"),
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve daily snapshots of social media insights (followers, reach, profile views, website clicks, saves).
    Completely fault-tolerant: returns empty list if table or data is not yet initialized.
    """
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).date()
        stmt = select(SocialMediaInsight).where(SocialMediaInsight.date >= cutoff)
        
        if platform and platform.lower() != "all":
            stmt = stmt.where(SocialMediaInsight.platform == platform.lower())
            
        stmt = stmt.order_by(SocialMediaInsight.date.desc())
        result = await db.execute(stmt)
        insights = result.scalars().all()
        return list(insights)
    except Exception as exc:
        logger.warning(f"Unable to query social_media_insights table (database may not be migrated yet): {exc}")
        return []

@router.post("/insights", summary="Upsert social media insights from n8n or API")
async def sync_social_insights(
    payload: Union[SocialInsightsSyncPayload, List[SocialInsightCreate], SocialInsightCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest daily insight metrics from n8n scheduled workflow or manual trigger.
    Upserts records matching (platform, account_id, date).
    """
    records_to_process: List[SocialInsightCreate] = []

    if isinstance(payload, list):
        records_to_process = payload
    elif isinstance(payload, SocialInsightsSyncPayload):
        if payload.insights:
            records_to_process = payload.insights
        elif payload.platform and payload.date:
            records_to_process = [SocialInsightCreate(
                platform=payload.platform,
                account_id=payload.account_id or "default",
                date=payload.date,
                total_followers=payload.total_followers or 0,
                reach=payload.reach or 0,
                profile_views=payload.profile_views or 0,
                website_clicks=payload.website_clicks or 0,
                saves=payload.saves or 0
            )]
    elif isinstance(payload, SocialInsightCreate):
        records_to_process = [payload]

    if not records_to_process:
        return {"success": True, "message": "No insight records to process", "processed_count": 0}

    upserted_count = 0
    try:
        for rec in records_to_process:
            # Parse date safely
            rec_date = rec.date
            if isinstance(rec_date, str):
                try:
                    parsed_date = datetime.strptime(rec_date[:10], "%Y-%m-%d").date()
                except Exception:
                    parsed_date = datetime.utcnow().date()
            elif isinstance(rec_date, datetime):
                parsed_date = rec_date.date()
            elif isinstance(rec_date, date):
                parsed_date = rec_date
            else:
                parsed_date = datetime.utcnow().date()

            platform_val = rec.platform.lower().strip()
            account_id_val = rec.account_id or "default"

            # Check for existing record
            stmt = select(SocialMediaInsight).where(
                and_(
                    SocialMediaInsight.platform == platform_val,
                    SocialMediaInsight.account_id == account_id_val,
                    SocialMediaInsight.date == parsed_date
                )
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.total_followers = rec.total_followers or existing.total_followers
                existing.reach = rec.reach or existing.reach
                existing.profile_views = rec.profile_views or existing.profile_views
                existing.website_clicks = rec.website_clicks or existing.website_clicks
                existing.saves = rec.saves or existing.saves
            else:
                new_insight = SocialMediaInsight(
                    platform=platform_val,
                    account_id=account_id_val,
                    date=parsed_date,
                    total_followers=rec.total_followers or 0,
                    reach=rec.reach or 0,
                    profile_views=rec.profile_views or 0,
                    website_clicks=rec.website_clicks or 0,
                    saves=rec.saves or 0
                )
                db.add(new_insight)

            upserted_count += 1

        await db.commit()
        return {
            "success": True,
            "message": f"Successfully processed {upserted_count} insight records",
            "processed_count": upserted_count
        }
    except Exception as exc:
        logger.error(f"Error upserting social media insights: {exc}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upsert social media insights: {str(exc)}"
        )

@router.post("/insights/seed", summary="Seed 30 days of realistic demo insights")
async def seed_demo_insights(
    db: AsyncSession = Depends(get_db)
):
    """
    Populate realistic demo metrics for Instagram and Facebook for the last 30 days.
    Allows the clinic to preview analytics before the daily n8n cron executes.
    """
    try:
        base_date = datetime.utcnow().date()
        inserted_count = 0

        # 30 days of Instagram data
        ig_followers = 3200
        for i in range(30, -1, -1):
            day_date = base_date - timedelta(days=i)
            ig_followers += (12 + (i % 7) * 3)
            reach_val = 1500 + ((i * 47) % 1800) + (800 if i % 6 == 0 else 0)
            profile_views_val = int(reach_val * 0.05) + (i % 15)
            clicks_val = int(profile_views_val * 0.22) + (i % 5)
            saves_val = int(clicks_val * 0.8) + (i % 4)

            # Check if exists
            stmt = select(SocialMediaInsight).where(
                and_(
                    SocialMediaInsight.platform == "instagram",
                    SocialMediaInsight.account_id == "default",
                    SocialMediaInsight.date == day_date
                )
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()

            if not existing:
                db.add(SocialMediaInsight(
                    platform="instagram",
                    account_id="default",
                    date=day_date,
                    total_followers=ig_followers,
                    reach=reach_val,
                    profile_views=profile_views_val,
                    website_clicks=clicks_val,
                    saves=saves_val
                ))
                inserted_count += 1

        # 30 days of Facebook data
        fb_followers = 4850
        for i in range(30, -1, -1):
            day_date = base_date - timedelta(days=i)
            fb_followers += (8 + (i % 5) * 2)
            reach_val = 900 + ((i * 31) % 1200) + (500 if i % 7 == 0 else 0)
            profile_views_val = int(reach_val * 0.04) + (i % 10)
            clicks_val = int(profile_views_val * 0.28) + (i % 4)
            saves_val = int(clicks_val * 0.3) + (i % 2)

            stmt = select(SocialMediaInsight).where(
                and_(
                    SocialMediaInsight.platform == "facebook",
                    SocialMediaInsight.account_id == "default",
                    SocialMediaInsight.date == day_date
                )
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()

            if not existing:
                db.add(SocialMediaInsight(
                    platform="facebook",
                    account_id="default",
                    date=day_date,
                    total_followers=fb_followers,
                    reach=reach_val,
                    profile_views=profile_views_val,
                    website_clicks=clicks_val,
                    saves=saves_val
                ))
                inserted_count += 1

        await db.commit()
        return {
            "success": True,
            "message": f"Successfully seeded {inserted_count} demo insight records",
            "count": inserted_count
        }
    except Exception as exc:
        logger.error(f"Error seeding demo insights: {exc}")
        await db.rollback()
        return {"success": False, "error": str(exc), "count": 0}

@router.delete("/insights", summary="Clear social media insights")
async def clear_social_insights(
    db: AsyncSession = Depends(get_db)
):
    """
    Clear all insight records (e.g. for testing clean empty states).
    """
    try:
        stmt = select(SocialMediaInsight)
        res = await db.execute(stmt)
        records = res.scalars().all()
        for r in records:
            await db.delete(r)
        await db.commit()
        return {"success": True, "message": "All insights cleared"}
    except Exception as exc:
        await db.rollback()
        return {"success": False, "error": str(exc)}


