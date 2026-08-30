"""FastAPI endpoints for Omnichannel Patient Bridge & AI Dossier Ingestion."""

import os
import re
from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import desc, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.database import get_db
from app.modules.agenda.models import Appointment, AppointmentStatusEvent, Cabinet
from app.modules.agenda.service import CabinetService
from app.modules.agenda.tz import as_utc, get_clinic_tz, safe_zone
from app.modules.patients.models import Patient
from .models import ChatMessage, ChatSessionState, PatientDossierFile, PatientLead
from .schemas import (
    AppointmentSyncResponse,
    BatchMessagesPayload,
    ChatMessageResponse,
    ChatStatusResponse,
    GenericSuccessResponse,
    InboundMessagePayload,
    IncomingAppointmentPayload,
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

    # Group by normalized phone so -1003937847791 and 1003937847791 merge into ONE thread
    threads_map: dict[str, dict] = {}
    for m in all_msgs:
        raw_phone = m.phone.strip()
        phone_key = normalize_phone(raw_phone) or raw_phone
        if phone_key not in threads_map:
            threads_map[phone_key] = {
                "id": f"thread-{phone_key}",
                "phone": raw_phone,
                "platform": m.platform or "telegram",
                "patient_id": str(m.patient_id) if m.patient_id else None,
                "name": raw_phone,
                "last_message": m.content,
                "last_time": m.sent_at.isoformat(),
                "is_human_active": False,
                "is_urgent": False,
                "has_radio": False,
                "messages": [],
            }
        
        # Check emergency keywords
        lower_content = (m.content or "").lower()
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
        raw_p = thread["phone"]

        # Lookup patient name
        try:
            patient = await find_patient_by_phone(db, raw_p)
            if not patient:
                patient = await find_patient_by_phone(db, phone_key)
            if patient:
                thread["name"] = f"{patient.first_name} {patient.last_name}"
                thread["patient_id"] = str(patient.id)
            else:
                # Lookup lead name
                lead_stmt = select(PatientLead).where(
                    or_(PatientLead.phone == raw_p, PatientLead.phone == phone_key)
                ).order_by(desc(PatientLead.created_at))
                lead_res = await db.execute(lead_stmt)
                lead = lead_res.scalars().first()
                if lead:
                    thread["name"] = lead.name
        except Exception:
            pass

        # Lookup takeover state & override urgency (fault tolerant)
        try:
            state_stmt = select(ChatSessionState).where(
                or_(ChatSessionState.phone == raw_p, ChatSessionState.phone == phone_key)
            )
            state_res = await db.execute(state_stmt)
            state = state_res.scalars().first()
            if state:
                thread["is_human_active"] = state.is_human_active
                if getattr(state, "is_urgent", None) is not None:
                    thread["is_urgent"] = state.is_urgent
        except Exception:
            pass

        # Check if patient has radios
        try:
            if thread.get("patient_id"):
                radio_stmt = select(PatientDossierFile).where(PatientDossierFile.patient_id == UUID(thread["patient_id"]))
                radio_res = await db.execute(radio_stmt)
                if radio_res.scalars().first():
                    thread["has_radio"] = True
        except Exception:
            pass

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


# --- 12. POST /appointments/sync (Google Calendar & Sheets Sync) ---
@router.post("/appointments/sync", response_model=AppointmentSyncResponse)
async def sync_incoming_appointment(
    payload: IncomingAppointmentPayload,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Synchronizes external bookings from Google Calendar / Sheets to DentalPin Agenda."""
    # 1. Verify Secret
    if not verify_n8n_secret(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing DENTALPIN_N8N_SECRET authorization header",
        )

    # 2. Resolve Clinic
    clinic_res = await db.execute(select(Clinic).limit(1))
    clinic = clinic_res.scalars().first()
    if not clinic:
        raise HTTPException(status_code=500, detail="No active clinic found")
    clinic_id = clinic.id

    # 3. Patient Resolution & Auto-Registration
    clean_phone = normalize_phone(payload.patient_phone)
    patient = await find_patient_by_phone(db, payload.patient_phone)
    if not patient:
        parts = payload.patient_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

        patient = Patient(
            clinic_id=clinic_id,
            first_name=first_name,
            last_name=last_name,
            phone=payload.patient_phone.strip(),
            status="active",
            notes=f"[Origine: Google Calendar / n8n — Synchronisé le {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}]",
        )
        db.add(patient)
        await db.flush()
        await db.refresh(patient)

    # Convert staged lead if exists
    lead_stmt = select(PatientLead).where(
        or_(PatientLead.phone == payload.patient_phone, PatientLead.phone == clean_phone)
    )
    lead_res = await db.execute(lead_stmt)
    lead = lead_res.scalars().first()
    if lead:
        lead.stage = "converted"
        lead.patient_id = patient.id

    # 4. Deterministic Doctor Resolution
    doctor: Optional[User] = None
    if payload.doctor_email:
        doc_stmt = (
            select(User)
            .join(ClinicMembership, ClinicMembership.user_id == User.id)
            .where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.is_professional.is_(True),
                User.email == payload.doctor_email.strip().lower(),
            )
        )
        doctor = (await db.execute(doc_stmt)).scalars().first()

    if not doctor:
        # Prioritize primary Dentist / Admin Doctor
        doc_stmt = (
            select(User)
            .join(ClinicMembership, ClinicMembership.user_id == User.id)
            .where(
                ClinicMembership.clinic_id == clinic_id,
                ClinicMembership.is_professional.is_(True),
                ClinicMembership.role.in_(["dentist", "admin"]),
            )
            .order_by(
                ClinicMembership.role == "dentist",
                User.created_at.asc(),
            )
        )
        doctor = (await db.execute(doc_stmt)).scalars().first()

    if not doctor:
        fallback_stmt = select(User).join(ClinicMembership, ClinicMembership.user_id == User.id).where(ClinicMembership.clinic_id == clinic_id)
        doctor = (await db.execute(fallback_stmt)).scalars().first()

    if not doctor:
        raise HTTPException(status_code=500, detail="No doctor available to assign appointment")

    # 5. Timezone & Duration Normalization
    clinic_tz = await get_clinic_tz(db, clinic_id)
    try:
        start_raw = payload.start_time.replace("Z", "+00:00")
        start_dt = datetime.fromisoformat(start_raw)
        start_utc = as_utc(start_dt, clinic_tz)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid start_time format: {e}")

    if payload.end_time:
        try:
            end_raw = payload.end_time.replace("Z", "+00:00")
            end_dt = datetime.fromisoformat(end_raw)
            end_utc = as_utc(end_dt, clinic_tz)
        except Exception:
            end_utc = start_utc + timedelta(minutes=30)
    else:
        end_utc = start_utc + timedelta(minutes=30)

    # 6. Cabinet Resolution
    cabinet_id = None
    cabinet_name = None
    if payload.cabinet_name:
        cab = await CabinetService.get_by_name(db, clinic_id, payload.cabinet_name.strip())
        if cab:
            cabinet_id = cab.id
            cabinet_name = cab.name

    # 7. Check for existing appointment by external_id or matching patient slot
    existing_apt = None
    if payload.external_id:
        apt_stmt = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.external_id == payload.external_id,
        )
        apt_res = await db.execute(apt_stmt)
        existing_apt = apt_res.scalars().first()

    if not existing_apt:
        # Check if patient already booked at this exact start time
        pt_apt_stmt = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.patient_id == patient.id,
            Appointment.start_time == start_utc,
            Appointment.status != "cancelled",
        )
        pt_apt_res = await db.execute(pt_apt_stmt)
        existing_apt = pt_apt_res.scalars().first()

    existing_id = existing_apt.id if existing_apt else None

    # Check if cabinet slot is occupied by a DIFFERENT active appointment
    if cabinet_id:
        slot_stmt = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.cabinet_id == cabinet_id,
            Appointment.professional_id == doctor.id,
            Appointment.start_time == start_utc,
            Appointment.status != "cancelled",
        )
        if existing_id:
            slot_stmt = slot_stmt.where(Appointment.id != existing_id)
        slot_res = await db.execute(slot_stmt)
        occupied = slot_res.scalars().first()
        if occupied:
            # Try alternate active cabinets
            cabinets = await CabinetService.list_cabinets(db, clinic_id)
            found_free = False
            for alt_cab in cabinets:
                if alt_cab.id != cabinet_id:
                    alt_stmt = select(Appointment).where(
                        Appointment.clinic_id == clinic_id,
                        Appointment.cabinet_id == alt_cab.id,
                        Appointment.professional_id == doctor.id,
                        Appointment.start_time == start_utc,
                        Appointment.status != "cancelled",
                    )
                    if existing_id:
                        alt_stmt = alt_stmt.where(Appointment.id != existing_id)
                    if not (await db.execute(alt_stmt)).scalars().first():
                        cabinet_id = alt_cab.id
                        cabinet_name = alt_cab.name
                        found_free = True
                        break
            if not found_free:
                # Place in unassigned chair to prevent slot unique violation
                cabinet_id = None
                cabinet_name = None
    elif not cabinet_id:
        cabinets = await CabinetService.list_cabinets(db, clinic_id)
        if cabinets:
            # Find first free cabinet
            for cab in cabinets:
                slot_stmt = select(Appointment).where(
                    Appointment.clinic_id == clinic_id,
                    Appointment.cabinet_id == cab.id,
                    Appointment.professional_id == doctor.id,
                    Appointment.start_time == start_utc,
                    Appointment.status != "cancelled",
                )
                if existing_id:
                    slot_stmt = slot_stmt.where(Appointment.id != existing_id)
                if not (await db.execute(slot_stmt)).scalars().first():
                    cabinet_id = cab.id
                    cabinet_name = cab.name
                    break

    action = "created"
    if existing_apt:
        existing_apt.patient_id = patient.id
        existing_apt.professional_id = doctor.id
        existing_apt.cabinet_id = cabinet_id
        existing_apt.cabinet = cabinet_name
        existing_apt.start_time = start_utc
        existing_apt.end_time = end_utc
        existing_apt.treatment_type = payload.treatment_type or existing_apt.treatment_type
        existing_apt.status = payload.status or "confirmed"
        existing_apt.source = "google_calendar"
        existing_apt.external_id = payload.external_id or existing_apt.external_id
        appointment = existing_apt
        action = "updated"
    else:
        appointment = Appointment(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=patient.id,
            professional_id=doctor.id,
            cabinet_id=cabinet_id,
            cabinet=cabinet_name,
            start_time=start_utc,
            end_time=end_utc,
            treatment_type=payload.treatment_type or "Consultation",
            status=payload.status or "confirmed",
            external_id=payload.external_id,
            source="google_calendar",
            current_status_since=datetime.now(UTC),
        )
        db.add(appointment)

    try:
        await db.flush()
        if action == "created":
            status_event = AppointmentStatusEvent(
                id=uuid4(),
                clinic_id=clinic_id,
                appointment_id=appointment.id,
                from_status=None,
                to_status=appointment.status,
                changed_by=doctor.id,
            )
            db.add(status_event)
        await db.commit()
    except Exception as err:
        await db.rollback()
        # Fallback to unassigned cabinet (deferred chair) to guarantee insertion without error
        if existing_id:
            clean_apt = (await db.execute(select(Appointment).where(Appointment.id == existing_id))).scalars().first()
            if clean_apt:
                clean_apt.cabinet_id = None
                clean_apt.cabinet = None
                clean_apt.start_time = start_utc
                clean_apt.end_time = end_utc
                clean_apt.status = payload.status or "confirmed"
                await db.commit()
                appointment = clean_apt
        else:
            fallback_apt = Appointment(
                id=uuid4(),
                clinic_id=clinic_id,
                patient_id=patient.id,
                professional_id=doctor.id,
                cabinet_id=None,
                cabinet=None,
                start_time=start_utc,
                end_time=end_utc,
                treatment_type=payload.treatment_type or "Consultation",
                status=payload.status or "confirmed",
                external_id=payload.external_id,
                source="google_calendar",
                current_status_since=datetime.now(UTC),
            )
            db.add(fallback_apt)
            await db.commit()
            appointment = fallback_apt

    await db.refresh(appointment)

    start_local = appointment.start_time.astimezone(clinic_tz).isoformat()

    return AppointmentSyncResponse(
        success=True,
        action=action,
        appointment_id=str(appointment.id),
        patient_id=str(patient.id),
        doctor_name=f"{doctor.first_name} {doctor.last_name}",
        cabinet=appointment.cabinet,
        start_time_local=start_local,
        message=f"Appointment {action} successfully for {patient.first_name} {patient.last_name}",
    )



