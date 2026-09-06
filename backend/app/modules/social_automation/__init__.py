from fastapi import APIRouter
from app.core.plugins import BaseModule
from .router import router
from .models import SocialPost, SocialMediaInsight

class SocialAutomationModule(BaseModule):
    """n8n Social Media Content Validation & Performance Analytics Studio."""

    manifest = {
        "name": "social_automation",
        "version": "1.1.0",
        "summary": "n8n Social Media Content Validation & Performance Analytics Studio",
        "author": "DentalPin Setup",
        "license": "BSL-1.1",
        "category": "official",
        "depends": [],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "owner": ["*"],
            "admin": ["*"],
            "doctor": ["*"],
            "assistant": ["read", "reports.read"],
            "receptionist": ["read", "reports.read"],
        },
        "frontend": {
            "navigation": [
                {
                    "label": "nav.social",
                    "icon": "i-lucide-share-2",
                    "to": "/social/posts",
                    "order": 850,
                },
                {
                    "label": "nav.socialReports",
                    "icon": "i-lucide-bar-chart-2",
                    "to": "/social/reports",
                    "order": 851,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [SocialPost, SocialMediaInsight]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write", "reports.read", "reports.write"]

