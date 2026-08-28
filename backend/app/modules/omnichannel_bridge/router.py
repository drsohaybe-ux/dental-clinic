"""FastAPI endpoints for Omnichannel Patient Bridge & AI Dossier Ingestion."""

import os
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.patients.models import Patient
from .models import ChatMessage, ChatSessionState, PatientDossierFile, PatientLead
from .schemas import (
    BatchMessagesPayload,
    ChatMessageResponse,
    ChatStatusResponse,
    GenericSuccessResponse,
    InboundMessagePayload,
    IncomingLeadPayload,
    OutboundMessagePayload,
    PatientDossierPayload,
    PatientDossierResponse,
)

router = APIRouter(tags=["omnichannel_bridge"])


def normalize_phone(phone: str) -> str:
    """Normalize phone number to strip whitespace, dashes, and standard prefixes."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("213") and len(digits) > 9:
        return digits[3:]
    if digits.startswith("0") and len(digits) > 8:
        return digits[1:]
    return digits


async def find_patient_by_phone(db: AsyncSession, phone: str) -> Optional[Patient]:
    """Finds a registered patient matching the normalized phone number."""
    clean = normalize_phone(phone)
    if not clean:
        return None

    # Search with variations
    stmt = select(Patient).where(
        or_(
            Patient.phone.ilike(f"%{clean}%"),
            Patient.phone.ilike(f"%{phone}%"),
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()


def verify_n8n_secret(authorization: Optional[str] = Header(None)) -> bool:
    """Optional validation of DENTALPIN_N8N_SECRET token."""
    expected = os.environ.get("DENTALPIN_N8N_SECRET")
    if not expected:
        return True
    if not authorization:
        return True  # If no header sent but webhook configured
    token = authorization.replace("Bearer ", "").strip()
    return token == expected.strip()


# --- 1. GET /chats/status ---
@router.get("/chats/status", response_model=ChatStatusResponse)
async def get_chat_status(
    phone: str = Query(..., description="Patient phone number"),
    db: AsyncSession = Depends(get_db),
):
    """
    Checks if a human doctor has taken over the chat, finds the patient ID,
    and checks for active bookings.
    """
    clean = normalize_phone(phone)
    patient = await find_patient_by_phone(db, phone)

    # Check human takeover state
    state_stmt = select(ChatSessionState).where(
        or_(
            ChatSessionState.phone == phone,
            ChatSessionState.phone == clean,
            ChatSessionState.phone.ilike(f"%{clean}%"),
        )
    )
    state_res = await db.execute(state_stmt)
    session_state = state_res.scalars().first()
    is_human = session_state.is_human_active if session_state else False

    # Check active booking (has patient and status active)
    has_active_booking = bool(patient and patient.status == "active")

    return ChatStatusResponse(
        is_human_active=is_human,
        patient_id=str(patient.id) if patient else None,
        has_active_booking=has_active_booking,
    )


# --- 2. POST /messages/inbound ---
@router.post("/messages/inbound", response_model=GenericSuccessResponse)
async def log_inbound_message(
    payload: InboundMessagePayload,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Logs incoming messages from patients (Telegram, WhatsApp)."""
    identifier = payload.get_identifier()
    patient = await find_patient_by_phone(db, identifier)

    # Auto-stage lead if name is provided
    sender_name = payload.name or payload.full_name
    if sender_name:
        clean_id = normalize_phone(identifier)
        lead_stmt = select(PatientLead).where(
            or_(PatientLead.phone == identifier, PatientLead.phone == clean_id)
        )
        lead_res = await db.execute(lead_stmt)
        existing_lead = lead_res.scalars().first()
        if existing_lead:
            existing_lead.name = sender_name
        else:
            new_lead = PatientLead(
                name=sender_name,
                phone=identifier,
                source=payload.platform or "telegram",
                stage="new",
            )
            db.add(new_lead)

    # Auto-stage urgency if flagged
    if payload.is_urgent:
        clean_id = normalize_phone(identifier)
        state_stmt = select(ChatSessionState).where(
            or_(ChatSessionState.phone == identifier, ChatSessionState.phone == clean_id)
        )
        state_res = await db.execute(state_stmt)
        state = state_res.scalars().first()
        if not state:
            state = ChatSessionState(phone=identifier, is_urgent=True)
            db.add(state)
        else:
            state.is_urgent = True

    msg = ChatMessage(
        phone=identifier,
        sender="patient",
        content=payload.content,
        platform=payload.platform or "telegram",
        patient_id=patient.id if patient else None,
        sent_at=datetime.utcnow(),
    )
    db.add(msg)
    await db.commit()

    return GenericSuccessResponse(
        success=True,
        message="Inbound message recorded successfully",
        id=str(msg.id),
    )


# --- 3. POST /messages/outbound ---
@router.post("/messages/outbound", response_model=GenericSuccessResponse)
async def log_outbound_message(
    payload: OutboundMessagePayload,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Logs outgoing AI or doctor replies to the patient."""
    identifier = payload.get_identifier()
    patient = await find_patient_by_phone(db, identifier)

    # Auto-stage lead if name is provided
    sender_name = payload.name or payload.full_name
    if sender_name:
        clean_id = normalize_phone(identifier)
        lead_stmt = select(PatientLead).where(
            or_(PatientLead.phone == identifier, PatientLead.phone == clean_id)
        )
        lead_res = await db.execute(lead_stmt)
        existing_lead = lead_res.scalars().first()
        if existing_lead:
            existing_lead.name = sender_name
        else:
            new_lead = PatientLead(
                name=sender_name,
                phone=identifier,
                source="telegram",
                stage="new",
            )
            db.add(new_lead)

    # Auto-stage urgency if flagged
    if payload.is_urgent:
        clean_id = normalize_phone(identifier)
        state_stmt = select(ChatSessionState).where(
            or_(ChatSessionState.phone == identifier, ChatSessionState.phone == clean_id)
        )
        state_res = await db.execute(state_stmt)
        state = state_res.scalars().first()
        if not state:
            state = ChatSessionState(phone=identifier, is_urgent=True)
            db.add(state)
        else:
            state.is_urgent = True

    msg = ChatMessage(
        phone=identifier,
        sender=payload.sender or "ai_bot",
        content=payload.content,
        platform="telegram",
        patient_id=patient.id if patient else None,
        sent_at=datetime.utcnow(),
    )
    db.add(msg)
    await db.commit()

    return GenericSuccessResponse(
        success=True,
        message="Outbound message recorded successfully",
        id=str(msg.id),
    )


# --- 3b. POST /messages/batch (Initial 10-Message History Ingestion) ---
@router.post("/messages/batch", response_model=GenericSuccessResponse)
async def log_batch_messages(
    payload: BatchMessagesPayload,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Saves initial past history batch (e.g. 10 messages) to PostgreSQL."""
    patient = await find_patient_by_phone(db, payload.phone)
    inserted_count = 0

    for item in payload.messages:
        # Check duplicate
        existing = await db.execute(
            select(ChatMessage).where(
                ChatMessage.phone == payload.phone,
                ChatMessage.content == item.content,
                ChatMessage.sender == item.sender,
            )
        )
        if not existing.scalars().first():
            msg = ChatMessage(
                phone=payload.phone,
                sender=item.sender,
                content=item.content,
                platform=item.platform or "telegram",
                patient_id=patient.id if patient else None,
                sent_at=datetime.utcnow(),
            )
            db.add(msg)
            inserted_count += 1

    await db.commit()
    return GenericSuccessResponse(
        success=True,
        message=f"{inserted_count} past messages saved to PostgreSQL history",
    )


# --- 4. POST /automation/incoming-lead ---
@router.post("/automation/incoming-lead", response_model=GenericSuccessResponse)
async def register_incoming_lead(
    payload: IncomingLeadPayload,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Stages incoming prospective leads from Telegram/WhatsApp without spamming active patient tables."""
    lead = PatientLead(
        name=payload.name,
        phone=payload.phone,
        source=payload.source or "telegram",
        stage=payload.stage or "new",
        notes=payload.notes,
    )
    db.add(lead)
    await db.commit()

    return GenericSuccessResponse(
        success=True,
        message="Lead registered and staged successfully",
        id=str(lead.id),
    )


# --- 5. POST /patients/dossier ---
@router.post("/patients/dossier", response_model=GenericSuccessResponse)
async def save_patient_dossier_file(
    payload: PatientDossierPayload,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Saves radiographs (panoramic X-rays) and AI clinical analyses into the patient file."""
    patient = await find_patient_by_phone(db, payload.phone)

    dossier = PatientDossierFile(
        phone=payload.phone,
        name=payload.name or "Patient Radio",
        file_type=payload.file_type or "xray_panoramic",
        file_url=payload.file_url,
        ai_analysis=payload.ai_analysis,
        status=payload.status or "pending_consultation",
        patient_id=patient.id if patient else None,
    )
    db.add(dossier)
    await db.commit()

    return GenericSuccessResponse(
        success=True,
        message="Radiograph & AI diagnostic analysis attached to dossier",
        id=str(dossier.id),
    )


# --- 6. GET /patients/{patient_id}/dossier-files (For UI) ---
@router.get("/patients/{patient_id}/dossier-files", response_model=list[PatientDossierResponse])
async def get_patient_dossier_files(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all radiographs and AI analyses for a specific patient."""
    try:
        pid = UUID(patient_id)
        stmt = select(PatientDossierFile).where(PatientDossierFile.patient_id == pid).order_by(desc(PatientDossierFile.created_at))
        res = await db.execute(stmt)
        files = res.scalars().all()
        return [
            PatientDossierResponse(
                id=str(f.id),
                phone=f.phone,
                name=f.name,
                file_type=f.file_type,
                file_url=f.file_url,
                ai_analysis=f.ai_analysis,
                status=f.status,
                created_at=f.created_at,
            )
            for f in files
        ]
    except Exception:
        return []


# --- 7. GET /patients/{patient_id}/chat-history (For UI) ---
@router.get("/patients/{patient_id}/chat-history", response_model=list[ChatMessageResponse])
async def get_patient_chat_history(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves 2-way chat dialogue (Patient + AI bot + Doctor) for the patient profile."""
    try:
        pid = UUID(patient_id)
        stmt = select(ChatMessage).where(ChatMessage.patient_id == pid).order_by(ChatMessage.sent_at)
        res = await db.execute(stmt)
        messages = res.scalars().all()
        return [
            ChatMessageResponse(
                id=str(m.id),
                phone=m.phone,
                sender=m.sender,
                content=m.content,
                platform=m.platform,
                sent_at=m.sent_at,
            )
            for m in messages
        ]
    except Exception:
        return []


# --- 8. POST /chats/takeover (Toggle Human Mode) ---
@router.post("/chats/takeover", response_model=GenericSuccessResponse)
async def toggle_human_takeover(
    phone: str = Query(...),
    active: bool = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Toggles human doctor takeover flag for a phone number."""
    clean = normalize_phone(phone)
    stmt = select(ChatSessionState).where(
        or_(
            ChatSessionState.phone == phone,
            ChatSessionState.phone == clean,
        )
    )
    res = await db.execute(stmt)
    state = res.scalars().first()

    if not state:
        state = ChatSessionState(
            phone=phone,
            is_human_active=active,
            last_takeover_at=datetime.utcnow() if active else None,
        )
        db.add(state)
    else:
        state.is_human_active = active
        if active:
            state.last_takeover_at = datetime.utcnow()

    await db.commit()
    status_text = "Human Takeover Active (AI Paused)" if active else "AI Assistant Active"
    return GenericSuccessResponse(success=True, message=status_text)


# --- 8b. POST /chats/urgency (Toggle Emergency State & De-escalate) ---
@router.post("/chats/urgency", response_model=GenericSuccessResponse)
async def toggle_chat_urgency(
    phone: str = Query(...),
    active: bool = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Sets or de-escalates emergency status for a conversation."""
    clean = normalize_phone(phone)
    stmt = select(ChatSessionState).where(
        or_(
            ChatSessionState.phone == phone,
            ChatSessionState.phone == clean,
        )
    )
    res = await db.execute(stmt)
    state = res.scalars().first()

    if not state:
        state = ChatSessionState(
            phone=phone,
            is_urgent=active,
        )
        db.add(state)
    else:
        state.is_urgent = active

    await db.commit()
    msg = "Statut Urgence activé 🚨" if active else "Statut Urgence retiré avec succès ✅"
    return GenericSuccessResponse(success=True, message=msg)


# --- 9. GET /conversations (Aggregated Live Threads for Dashboard) ---
@router.get("/conversations")
async def get_live_conversations(
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregated conversation threads for the Messagerie dashboard."""
    stmt = select(ChatMessage).order_by(desc(ChatMessage.sent_at)).limit(200)
    res = await db.execute(stmt)
    all_msgs = res.scalars().all()

    # Group by phone
    threads_map: dict[str, dict] = {}
    for m in all_msgs:
        phone_key = m.phone.strip()
        if phone_key not in threads_map:
            threads_map[phone_key] = {
                "id": f"thread-{phone_key}",
                "phone": phone_key,
                "platform": m.platform or "telegram",
                "patient_id": str(m.patient_id) if m.patient_id else None,
                "name": phone_key,
                "last_message": m.content,
                "last_time": m.sent_at.isoformat(),
                "is_human_active": False,
                "is_urgent": False,
                "has_radio": False,
                "messages": [],
            }
        
        # Check emergency keywords
        lower_content = m.content.lower()
        if any(kw in lower_content for kw in ["douleur", "urgence", "saignement", "abces", "abcès", "dent cassee", "dent cassée", "rage de dent", "gonfle", "gonflé", "infection", "wja3", "darssa", "sater"]):
            threads_map[phone_key]["is_urgent"] = True

        if len(threads_map[phone_key]["messages"]) < 10:
            threads_map[phone_key]["messages"].append({
                "id": str(m.id),
                "sender": m.sender,
                "content": m.content,
                "time": m.sent_at.strftime("%H:%M"),
            })

    # Enrich with Patient / Lead names and Session States
    for phone_key, thread in threads_map.items():
        thread["messages"].reverse() # Chronological 10 past preview messages
        clean = normalize_phone(phone_key)

        # Lookup patient name
        patient = await find_patient_by_phone(db, phone_key)
        if patient:
            thread["name"] = f"{patient.first_name} {patient.last_name}"
            thread["patient_id"] = str(patient.id)
        else:
            # Lookup lead name
            lead_stmt = select(PatientLead).where(
                or_(PatientLead.phone == phone_key, PatientLead.phone == clean)
            ).order_by(desc(PatientLead.created_at))
            lead_res = await db.execute(lead_stmt)
            lead = lead_res.scalars().first()
            if lead:
                thread["name"] = lead.name

        # Lookup takeover state & override urgency
        state_stmt = select(ChatSessionState).where(
            or_(ChatSessionState.phone == phone_key, ChatSessionState.phone == clean)
        )
        state_res = await db.execute(state_stmt)
        state = state_res.scalars().first()
        if state:
            thread["is_human_active"] = state.is_human_active
            if state.is_urgent is not None:
                thread["is_urgent"] = state.is_urgent

        # Check if patient has radios
        if thread.get("patient_id"):
            radio_stmt = select(PatientDossierFile).where(PatientDossierFile.patient_id == UUID(thread["patient_id"]))
            radio_res = await db.execute(radio_stmt)
            if radio_res.scalars().first():
                thread["has_radio"] = True

    return list(threads_map.values())


# --- 10. GET /leads (Fetch Staged Prospects from DB) ---
@router.get("/leads")
async def get_all_leads(
    db: AsyncSession = Depends(get_db),
):
    """Returns all leads staged in the database."""
    stmt = select(PatientLead).order_by(desc(PatientLead.created_at)).limit(100)
    res = await db.execute(stmt)
    leads = res.scalars().all()

    result = []
    for l in leads:
        patient = await find_patient_by_phone(db, l.phone)
        result.append({
            "id": str(l.id),
            "name": l.name,
            "phone": l.phone,
            "source": l.source,
            "stage": "converted" if patient or l.stage == "converted" else l.stage,
            "notes": l.notes,
            "patient_id": str(patient.id) if patient else None,
            "created_at": l.created_at.strftime("%d/%m/%Y %H:%M") if l.created_at else "Récemment",
        })
    return result


# --- 11. POST /leads/convert (Persist Lead Conversion in DB) ---
@router.post("/leads/convert", response_model=GenericSuccessResponse)
async def convert_lead_in_db(
    phone: str = Query(...),
    patient_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Marks a lead as converted in PostgreSQL."""
    clean = normalize_phone(phone)
    stmt = select(PatientLead).where(
        or_(PatientLead.phone == phone, PatientLead.phone == clean)
    )
    res = await db.execute(stmt)
    leads = res.scalars().all()

    for l in leads:
        l.stage = "converted"
        if patient_id:
            try:
                l.patient_id = UUID(patient_id)
            except Exception:
                pass

    await db.commit()
    return GenericSuccessResponse(success=True, message="Lead permanently marked as converted")


