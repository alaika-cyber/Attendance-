from pydantic import BaseModel


class NotificationItem(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    severity: str
    metadata_json: str | None
    is_read: bool
    created_at: str


class MarkNotificationReadResponse(BaseModel):
    id: int
    is_read: bool
