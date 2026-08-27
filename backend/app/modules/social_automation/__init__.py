from app.core.module import Module
from .router import router

class SocialAutomationModule(Module):
    name = "social_automation"
    description = "n8n Social Media Content Validation Studio"
    routers = [router]
