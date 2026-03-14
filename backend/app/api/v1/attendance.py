from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_student, get_db_session
from app.core.config import get_settings
from app.services.geofence_settings_service import get_geofence
from app.schemas.attendance import AttendanceMarkRequest, AttendanceMarkResponse
from app.services.attendance_service import mark_attendance

router = APIRouter(prefix="/attendance", tags=["attendance"])
settings = get_settings()


@router.post("/mark", response_model=AttendanceMarkResponse)
def mark_attendance_api(
    payload: AttendanceMarkRequest,
    student=Depends(get_current_student),
    db: Session = Depends(get_db_session),
):
    geofence = get_geofence(db)
    geofence_lat = geofence.latitude if geofence else settings.geofence_lat
    geofence_lon = geofence.longitude if geofence else settings.geofence_lon
    geofence_radius = geofence.radius_meters if geofence else settings.geofence_radius_meters

    record = mark_attendance(
        db=db,
        student=student,
        class_code=payload.class_code,
        session_date=payload.session_date,
        latitude=payload.latitude,
        longitude=payload.longitude,
        image_b64=payload.live_image_b64,
        geofence_lat=geofence_lat,
        geofence_lon=geofence_lon,
        geofence_radius_m=geofence_radius,
        max_spoof_score=settings.max_spoof_score,
    )
    return AttendanceMarkResponse(attendance_id=record.id, status=record.status)
