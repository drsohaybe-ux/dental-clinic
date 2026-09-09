"""prescriptions — Doctor prescription pad (Ordonnance) module.

Generates and manages official medical prescriptions for patients, featuring
authentic Algerian prescription pad formatting (bilingual doctor headers in
French and Arabic, clinic branding, patient demographics, numbered medication
posology with duration, and footer with doctor signature/stamp space).
"""

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import Prescription, PrescriptionItem
from .router import router


class PrescriptionsModule(BaseModule):
    """Doctor prescription pad (Ordonnance) management."""

    manifest = {
        "name": "prescriptions",
        "version": "0.1.0",
        "summary": "Doctor prescription pad (Ordonnance) with authentic Algerian layout and printing.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients", "medication_catalog"],
        "installable": True,
        "auto_install": True,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read", "write"],
            "hygienist": ["read"],
            "assistant": ["read"],
            "receptionist": ["read"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return [Prescription, PrescriptionItem]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]
