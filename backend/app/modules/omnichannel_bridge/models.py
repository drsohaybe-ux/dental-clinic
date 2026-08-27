"""Database models for Omnichannel Bridge (n8n, Telegram, WhatsApp, AI Vision Dossier)."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class ChatMessage(Base, TimestampMixin):
    """Stores inbound and outbound patient communications from Telegram / WhatsApp / n8n."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=True)
    patient_id: Mapped[UUID | None] = mapped_column(ForeignKey("patients.id"), index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), index=True)
    sender: Mapped[str] = mapped_column(String(20))  # "patient", "ai_bot", "doctor", "staff"
    content: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(50), default="telegram")  # "telegram", "whatsapp", "manual"
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PatientLead(Base, TimestampMixin):
    """Stores staged inquiries/leads before they book an appointment."""

    __tablename__ = "patient_leads"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(50), index=True)
    source: Mapped[str] = mapped_column(String(50), default="telegram")
    stage: Mapped[str] = mapped_column(String(50), default="new")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False)


class PatientDossierFile(Base, TimestampMixin):
    """Stores radiographs and AI diagnostic analyses ingested from n8n vision."""

    __tablename__ = "patient_dossier_files"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=True)
    patient_id: Mapped[UUID | None] = mapped_column(ForeignKey("patients.id"), index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(200))
    file_type: Mapped[str] = mapped_column(String(50), default="xray_panoramic")
    file_url: Mapped[str] = mapped_column(Text)
    ai_analysis: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending_consultation")


class ChatSessionState(Base, TimestampMixin):
    """Tracks whether a human doctor has taken over a conversation."""

    __tablename__ = "chat_session_states"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id"), index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_human_active: Mapped[bool] = mapped_column(Boolean, default=False)
    last_takeover_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
