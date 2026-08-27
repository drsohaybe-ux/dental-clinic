from fastapi import APIRouter
from app.core.plugins import BaseModule
from .router import router
from .models import SocialPost

class SocialAutomationModule(BaseModule):
    """n8n Social Media Content Validation Studio."""

    manifest = {
        "name": "social_automation",
        "version": "1.0.0",
        "summary": "n8n Social Media Content Validation Studio",
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
            "assistant": ["read"],
            "receptionist": ["read"],
        },
        "frontend": {
            "navigation": [
                {
                    "label": "social.title",
                    "icon": "i-lucide-share-2",
                    "to": "/social/posts",
                    "permission": "social_automation.read",
                    "order": 95,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [SocialPost]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write"]
