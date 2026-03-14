from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin
from app.core.config import get_settings
from app.models import ApprovalStatus, Classroom, SpoofEvent, Student, User
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
from app.services.email_service import send_approval_email
from app.services.geofence_settings_service import get_geofence, upsert_geofence
from app.services.timetable_service import create_schedule, delete_schedule, list_schedules

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


@router.get("/spoof-alerts", response_model=list[SpoofAlertItem])
def spoof_alerts(
    limit: int = 20,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    rows = (
        db.query(SpoofEvent, Student, User, Classroom)
        .outerjoin(Student, Student.id == SpoofEvent.student_id)
        .outerjoin(User, User.id == Student.user_id)
        .outerjoin(Classroom, Classroom.id == SpoofEvent.classroom_id)
        .order_by(SpoofEvent.created_at.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )

    return [
        SpoofAlertItem(
            event_id=event.id,
            student_id=event.student_id,
            student_name=user.full_name if user else None,
            roll_no=student.roll_no if student else None,
            class_code=classroom.code if classroom else None,
            class_name=classroom.name if classroom else None,
            spoof_type=event.spoof_type,
            reason=event.reason,
            alert_status=event.alert_status,
            timestamp=event.created_at.isoformat(),
            evidence_image_b64=event.evidence_image_b64,
        )
        for event, student, user, classroom in rows
    ]


@router.get("/pending-approvals", response_model=list[PendingApprovalItem])
def pending_approvals(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    rows = (
        db.query(Student, User, Classroom)
        .join(User, User.id == Student.user_id)
        .join(Classroom, Classroom.id == Student.classroom_id)
        .filter(Student.approval_status == ApprovalStatus.PENDING)
        .order_by(Student.created_at.asc())
        .all()
    )

    return [
        PendingApprovalItem(
            student_id=student.id,
            full_name=user.full_name,
            email=user.email,
            roll_no=student.roll_no,
            class_code=classroom.code,
            class_name=classroom.name,
            academic_year=classroom.academic_year,
            captured_image_b64=student.captured_image_b64,
        )
        for student, user, classroom in rows
    ]


@router.post("/approve-student", response_model=ApprovalResponse)
def approve_student(
    payload: ApprovalRequest,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_approved = payload.approve
    student.approval_status = ApprovalStatus.APPROVED if payload.approve else ApprovalStatus.REJECTED
    student.approval_reason = payload.reason
    student.approval_decided_at = datetime.utcnow()

    user = db.query(User).filter(User.id == student.user_id).first()

    db.commit()
    email_sent = False
    if user:
        email_sent = send_approval_email(
            to_email=user.email,
            full_name=user.full_name,
            approved=payload.approve,
            reason=payload.reason,
        )

    return ApprovalResponse(
        student_id=student.id,
        status=student.approval_status.value,
        email_notification_sent=email_sent,
    )


@router.get("/geofence", response_model=GeofenceResponse)
def get_admin_geofence(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    geofence = get_geofence(db)
    if not geofence:
        return GeofenceResponse(
            latitude=settings.geofence_lat,
            longitude=settings.geofence_lon,
            radius_meters=settings.geofence_radius_meters,
        )

    return GeofenceResponse(
        latitude=geofence.latitude,
        longitude=geofence.longitude,
        radius_meters=geofence.radius_meters,
    )


@router.put("/geofence", response_model=GeofenceResponse)
def update_admin_geofence(
    payload: GeofenceUpdateRequest,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    if payload.radius_meters <= 0:
        raise HTTPException(status_code=400, detail="Radius must be greater than zero")

    geofence = upsert_geofence(
        db,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_meters=payload.radius_meters,
    )
    return GeofenceResponse(
        latitude=geofence.latitude,
        longitude=geofence.longitude,
        radius_meters=geofence.radius_meters,
    )


@router.post("/timetable", response_model=TimetableItem)
def create_timetable(
    payload: TimetableCreateRequest,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    row = create_schedule(
        db,
        class_code=payload.class_code,
        class_name=payload.class_name,
        academic_year=payload.academic_year,
        subject_name=payload.subject_name,
        schedule_date=payload.schedule_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    classroom = db.query(Classroom).filter(Classroom.id == row.classroom_id).first()
    return TimetableItem(
        schedule_id=row.id,
        subject_name=row.subject_name,
        class_code=classroom.code,
        class_name=classroom.name,
        academic_year=classroom.academic_year,
        schedule_date=row.schedule_date,
        start_time=row.start_time,
        end_time=row.end_time,
    )


@router.get("/timetable", response_model=list[TimetableItem])
def get_timetable(
    class_code: str | None = None,
    schedule_date: str | None = None,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    rows = list_schedules(db, class_code=class_code, schedule_date=schedule_date)
    return [
        TimetableItem(
            schedule_id=row.id,
            subject_name=row.subject_name,
            class_code=classroom.code,
            class_name=classroom.name,
            academic_year=classroom.academic_year,
            schedule_date=row.schedule_date,
            start_time=row.start_time,
            end_time=row.end_time,
        )
        for row, classroom in rows
    ]


@router.delete("/timetable/{schedule_id}")
def remove_timetable(
    schedule_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    deleted = delete_schedule(db, schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"deleted": True}
