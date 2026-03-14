from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.models import Notification
from app.schemas.notification import MarkNotificationReadResponse, NotificationItem

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/my", response_model=list[NotificationItem])
def my_notifications(
    limit: int = 30,
    unread_only: bool = False,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    rows = query.order_by(Notification.created_at.desc()).limit(max(1, min(limit, 200))).all()
    return [
        NotificationItem(
            id=row.id,
            notification_type=row.notification_type,
            title=row.title,
            message=row.message,
            severity=row.severity,
            metadata_json=row.metadata_json,
            is_read=row.is_read,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


@router.post("/{notification_id}/read", response_model=MarkNotificationReadResponse)
def mark_read(
    notification_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    row = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")

    row.is_read = True
    db.commit()
    return MarkNotificationReadResponse(id=row.id, is_read=row.is_read)
