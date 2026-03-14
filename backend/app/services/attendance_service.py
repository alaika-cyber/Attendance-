from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Attendance, Classroom, FaceEmbedding, SpoofEvent, Student
from app.services.face_service import compare_embeddings, generate_embedding
from app.services.geofence_service import is_within_geofence
from app.services.liveness_service import estimate_spoof_score
from app.services.notification_service import (
    notify_low_attendance,
    notify_spoof_attempt,
    notify_suspicious_activity_if_needed,
)
from app.services.reports_service import get_student_attendance_stats
from app.services.timetable_service import get_attendance_status_for_now
from app.utils.image import decode_image_from_b64

settings = get_settings()


def mark_attendance(
    db: Session,
    student: Student,
    class_code: str,
    session_date: str,
    latitude: float,
    longitude: float,
    image_b64: str,
    geofence_lat: float,
    geofence_lon: float,
    geofence_radius_m: float,
    max_spoof_score: float,
) -> Attendance:
    today = datetime.now().strftime("%Y-%m-%d")
    if session_date != today:
        raise HTTPException(status_code=403, detail="Attendance can only be marked for today's scheduled class")

    classroom = db.query(Classroom).filter(Classroom.code == class_code).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    if classroom.id != student.classroom_id:
        raise HTTPException(status_code=403, detail="Classroom mismatch")

    attendance_status = get_attendance_status_for_now(
        db,
        classroom_id=classroom.id,
        schedule_date=session_date,
    )
    if not attendance_status:
        raise HTTPException(
            status_code=403,
            detail=(
                "Attendance not allowed now. Mark only at class start (Present) or between "
                "start and end time (Late)."
            ),
        )

    if not is_within_geofence(latitude, longitude, geofence_lat, geofence_lon, geofence_radius_m):
        raise HTTPException(status_code=403, detail="Outside allowed geofence")

    frame = decode_image_from_b64(image_b64)
    spoof_score = estimate_spoof_score(frame)
    if spoof_score > max_spoof_score:
        event = SpoofEvent(
            student_id=student.id,
            classroom_id=student.classroom_id,
            spoof_type="liveness_photo_replay",
            reason=f"Liveness check failed with score {spoof_score:.2f}",
            alert_status="new",
            evidence_image_b64=image_b64,
        )
        db.add(event)
        db.flush()
        notify_spoof_attempt(db, student=student, event=event, class_code=classroom.code)
        notify_suspicious_activity_if_needed(
            db,
            student=student,
            threshold=settings.suspicious_spoof_attempts_24h,
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Potential spoof attempt detected")

    face_embedding = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student.id).first()
    if not face_embedding:
        raise HTTPException(status_code=400, detail="No enrolled biometric profile")

    similarity = compare_embeddings(face_embedding.embedding, generate_embedding(image_b64))
    if similarity < 0.84:
        raise HTTPException(status_code=403, detail="Face mismatch")

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.student_id == student.id,
            Attendance.classroom_id == classroom.id,
            Attendance.session_date == session_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked")

    record = Attendance(
        student_id=student.id,
        classroom_id=classroom.id,
        session_date=session_date,
        status=attendance_status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    stats = get_student_attendance_stats(db, student.id)
    notify_low_attendance(
        db,
        student=student,
        attendance_percentage=stats["attendance_percentage"],
        threshold=settings.low_attendance_threshold_percent,
    )
    db.commit()

    return record
