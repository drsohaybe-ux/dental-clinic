"""Pydantic schemas matching the n8n webhook contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union, Any
from uuid import UUID
from pydantic import BaseModel, Field


# --- 1. Chat Status ---
class ChatStatusResponse(BaseModel):
    is_human_active: bool = False
    patient_id: Optional[str] = None
    has_active_booking: bool = False


# --- 2. Inbound Message ---
class InboundMessagePayload(BaseModel):
    phone: Optional[str] = None
    chat_id: Optional[Union[str, int]] = Field(default=None, alias="chat id")
    chatId: Optional[Union[str, int]] = None
    name: Optional[str] = None
    full_name: Optional[str] = Field(default=None, alias="full name")
    content: str
    platform: Optional[str] = "telegram"
    is_urgent: Optional[bool] = False
    timestamp: Optional[str] = None

    class Config:
        populate_by_name = True
        extra = "allow"

    def get_identifier(self) -> str:
        if self.phone:
            return str(self.phone)
        if self.chat_id is not None:
            return str(self.chat_id)
        if self.chatId is not None:
            return str(self.chatId)
        return "unknown"


# --- 3. Outbound Message ---
class OutboundMessagePayload(BaseModel):
    phone: Optional[str] = None
    chat_id: Optional[Union[str, int]] = Field(default=None, alias="chat id")
    chatId: Optional[Union[str, int]] = None
    name: Optional[str] = None
    full_name: Optional[str] = Field(default=None, alias="full name")
    content: str
    sender: Optional[str] = "ai_bot"
    is_urgent: Optional[bool] = False
    timestamp: Optional[str] = None

    class Config:
        populate_by_name = True
        extra = "allow"

    def get_identifier(self) -> str:
        if self.phone:
            return str(self.phone)
        if self.chat_id is not None:
            return str(self.chat_id)
        if self.chatId is not None:
            return str(self.chatId)
        return "unknown"


# --- 3b. Batch Messages (Initial History Sync) ---
class BatchMessageItem(BaseModel):
    phone: str
    chat_id: Optional[str] = None
    content: str
    sender: str = "patient" # 'patient' | 'ai_bot' | 'doctor'
    platform: Optional[str] = "telegram"
    timestamp: Optional[str] = None


class BatchMessagesPayload(BaseModel):
    phone: str
    chat_id: Optional[str] = None
    messages: list[BatchMessageItem]


# --- 4. Incoming Lead ---
class IncomingLeadPayload(BaseModel):
    name: str
    phone: str
    source: Optional[str] = "telegram"
    stage: Optional[str] = "new"
    notes: Optional[str] = None


# --- 5. Patient Dossier & X-Ray Analysis ---
class PatientDossierPayload(BaseModel):
    phone: str
    name: Optional[str] = None
    file_type: str = "xray_panoramic"
    file_url: str
    ai_analysis: str
    status: Optional[str] = "pending_consultation"


# --- Response Models ---
class GenericSuccessResponse(BaseModel):
    success: bool = True
    message: str
    id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    phone: str
    sender: str
    content: str
    platform: str
    sent_at: datetime


class PatientDossierResponse(BaseModel):
    id: str
    phone: str
    name: str
    file_type: str
    file_url: str
    ai_analysis: str
    status: str
    created_at: datetime
