from fastapi import APIRouter
from app.core.plugins import BaseModule
from .models import ChatMessage, PatientLead, PatientDossierFile, ChatSessionState
from .router import router

class OmnichannelBridgeModule(BaseModule):
    """Omnichannel Communication & AI Clinical Dossier Bridge for n8n/Telegram/WhatsApp."""

    manifest = {
        "name": "omnichannel_bridge",
        "version": "1.0.0",
        "summary": "Omnichannel Patient Communication & AI Dossier Ingestion",
        "author": "DentalPin Omnichannel Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "owner": ["*"],
            "admin": ["*"],
            "doctor": ["*"],
            "assistant": ["read", "write"],
            "receptionist": ["read", "write"],
        },
    }

    def get_models(self) -> list:
        return [ChatMessage, PatientLead, PatientDossierFile, ChatSessionState]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]
