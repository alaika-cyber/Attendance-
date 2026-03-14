from fastapi import APIRouter

from app.api.v1 import admin, analytics, attendance, auth, chatbot, health, notifications, registration

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(registration.router)
api_router.include_router(attendance.router)
api_router.include_router(admin.router)
api_router.include_router(analytics.router)
api_router.include_router(chatbot.router)
api_router.include_router(notifications.router)
