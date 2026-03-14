from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Notification, SpoofEvent, Student, User, UserRole


def _exists_recent(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    within_minutes: int = 60,
) -> bool:
    cutoff = datetime.utcnow() - timedelta(minutes=within_minutes)
    row = (
        db.query(Notification.id)
        .filter(
            Notification.user_id == user_id,
            Notification.notification_type == notification_type,
            Notification.title == title,
            Notification.created_at >= cutoff,
        )
        .first()
    )
    return row is not None


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "info",
    metadata_json: str | None = None,
    dedupe_minutes: int | None = 60,
) -> None:
    if dedupe_minutes and _exists_recent(
        db,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        within_minutes=dedupe_minutes,
    ):
        return

    db.add(
        Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
            metadata_json=metadata_json,
        )
    )


def create_admin_notifications(
    db: Session,
    notification_type: str,
    title: str,
    message: str,
    severity: str = "warning",
    metadata_json: str | None = None,
    dedupe_minutes: int | None = 60,
) -> None:
    admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).all()
    for admin in admins:
        create_notification(
            db,
            user_id=admin.id,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
            metadata_json=metadata_json,
            dedupe_minutes=dedupe_minutes,
        )


def notify_spoof_attempt(db: Session, student: Student, event: SpoofEvent, class_code: str) -> None:
    student_user = db.query(User).filter(User.id == student.user_id).first()
    if student_user:
        create_notification(
            db,
            user_id=student_user.id,
            notification_type="student_spoof_warning",
            title="Spoof Attempt Warning",
            message=(
                f"A spoof-like attendance attempt was detected for class {class_code} at "
                f"{event.created_at.isoformat()} and attendance was blocked."
            ),
            severity="warning",
            metadata_json=f'{{"spoof_event_id": {event.id}}}',
            dedupe_minutes=10,
        )

    create_admin_notifications(
        db,
        notification_type="admin_spoof_alert",
        title="Spoof Attempt Alert",
        message=(
            f"Student ID {student.id} triggered spoof detection in class {class_code} at "
            f"{event.created_at.isoformat()}."
        ),
        severity="critical",
        metadata_json=f'{{"spoof_event_id": {event.id}, "student_id": {student.id}}}',
        dedupe_minutes=5,
    )


def notify_suspicious_activity_if_needed(db: Session, student: Student, threshold: int = 3) -> None:
    since = datetime.utcnow() - timedelta(hours=24)
    spoof_count = (
        db.query(SpoofEvent.id)
        .filter(SpoofEvent.student_id == student.id, SpoofEvent.created_at >= since)
        .count()
    )

    if spoof_count < threshold:
        return

    create_admin_notifications(
        db,
        notification_type="admin_suspicious_activity",
        title="Suspicious Activity Detected",
        message=(
            f"Student ID {student.id} has {spoof_count} spoof attempts in the last 24 hours."
        ),
        severity="critical",
        metadata_json=(
            f'{{"student_id": {student.id}, "spoof_attempts_24h": {spoof_count}, '
            f'"threshold": {threshold}}}'
        ),
        dedupe_minutes=180,
    )


def notify_low_attendance(db: Session, student: Student, attendance_percentage: float, threshold: float) -> None:
    student_user = db.query(User).filter(User.id == student.user_id).first()
    if not student_user or attendance_percentage >= threshold:
        return

    create_notification(
        db,
        user_id=student_user.id,
        notification_type="student_low_attendance",
        title="Low Attendance Alert",
        message=(
            f"Your attendance is {attendance_percentage:.2f}% which is below the threshold of "
            f"{threshold:.2f}%."
        ),
        severity="warning",
        metadata_json=(
            f'{{"attendance_percentage": {attendance_percentage:.2f}, "threshold": {threshold:.2f}}}'
        ),
        dedupe_minutes=720,
    )


def notify_monthly_report_admin(db: Session, month: str, student_emails: int, admin_emails: int) -> None:
    create_admin_notifications(
        db,
        notification_type="admin_monthly_report",
        title="Monthly Report Generated",
        message=(
            f"Monthly attendance report for {month} generated. Student emails sent: "
            f"{student_emails}, admin emails sent: {admin_emails}."
        ),
        severity="info",
        metadata_json=f'{{"month": "{month}"}}',
        dedupe_minutes=1440,
    )
