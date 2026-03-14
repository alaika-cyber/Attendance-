from app.schemas.admin import (
    ApprovalRequest,
    ApprovalResponse,
    GeofenceResponse,
    GeofenceUpdateRequest,
    PendingApprovalItem,
    SpoofAlertItem,
    TimetableCreateRequest,
    TimetableItem,
)
from app.schemas.analytics import DashboardResponse, SpoofSummary, TopStudent
from app.schemas.attendance import AttendanceMarkRequest, AttendanceMarkResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.chatbot import ChatbotRequest, ChatbotResponse
from app.schemas.notification import MarkNotificationReadResponse, NotificationItem
from app.schemas.student import StudentRegistrationRequest, StudentRegistrationResponse

__all__ = [
    "ApprovalRequest",
    "ApprovalResponse",
    "GeofenceResponse",
    "GeofenceUpdateRequest",
    "PendingApprovalItem",
    "SpoofAlertItem",
    "TimetableCreateRequest",
    "TimetableItem",
    "DashboardResponse",
    "SpoofSummary",
    "TopStudent",
    "AttendanceMarkRequest",
    "AttendanceMarkResponse",
    "LoginRequest",
    "TokenResponse",
    "ChatbotRequest",
    "ChatbotResponse",
    "NotificationItem",
    "MarkNotificationReadResponse",
    "StudentRegistrationRequest",
    "StudentRegistrationResponse",
]
