from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Classroom, WeeklySchedule


def _validate_time_range(start_time: str, end_time: str) -> None:
    try:
        start = datetime.strptime(start_time, "%H:%M").time()
        end = datetime.strptime(end_time, "%H:%M").time()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Time must be in HH:MM format") from exc

    if start >= end:
        raise HTTPException(status_code=400, detail="Start time must be earlier than end time")


def get_or_create_classroom(
    db: Session,
    class_code: str,
    class_name: str | None,
    academic_year: str | None,
) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.code == class_code).first()
    if classroom:
        return classroom

    classroom = Classroom(
        code=class_code,
        name=class_name or class_code,
        academic_year=academic_year or datetime.utcnow().strftime("%Y-%Y"),
    )
    db.add(classroom)
    db.flush()
    return classroom


def create_schedule(
    db: Session,
    class_code: str,
    subject_name: str,
    schedule_date: str,
    start_time: str,
    end_time: str,
    class_name: str | None = None,
    academic_year: str | None = None,
) -> WeeklySchedule:
    _validate_time_range(start_time, end_time)

    classroom = get_or_create_classroom(db, class_code, class_name, academic_year)

    row = WeeklySchedule(
        classroom_id=classroom.id,
        subject_name=subject_name,
        schedule_date=schedule_date,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_schedules(
    db: Session,
    class_code: str | None = None,
    schedule_date: str | None = None,
) -> list[tuple[WeeklySchedule, Classroom]]:
    query = db.query(WeeklySchedule, Classroom).join(Classroom, Classroom.id == WeeklySchedule.classroom_id)
    if class_code:
        query = query.filter(Classroom.code == class_code)
    if schedule_date:
        query = query.filter(WeeklySchedule.schedule_date == schedule_date)

    return query.order_by(WeeklySchedule.schedule_date.asc(), WeeklySchedule.start_time.asc()).all()


def delete_schedule(db: Session, schedule_id: int) -> bool:
    row = db.query(WeeklySchedule).filter(WeeklySchedule.id == schedule_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def is_attendance_window_open(db: Session, classroom_id: int, schedule_date: str) -> bool:
    now = datetime.now()
    now_time = now.time()

    rows = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.classroom_id == classroom_id,
            WeeklySchedule.schedule_date == schedule_date,
        )
        .all()
    )

    for row in rows:
        start = datetime.strptime(row.start_time, "%H:%M").time()
        end = datetime.strptime(row.end_time, "%H:%M").time()
        if start <= now_time <= end:
            return True

    return False


def get_attendance_status_for_now(
    db: Session,
    classroom_id: int,
    schedule_date: str,
) -> str | None:
    now = datetime.now()
    now_time = now.time().replace(second=0, microsecond=0)

    rows = (
        db.query(WeeklySchedule)
        .filter(
            WeeklySchedule.classroom_id == classroom_id,
            WeeklySchedule.schedule_date == schedule_date,
        )
        .order_by(WeeklySchedule.start_time.asc())
        .all()
    )

    for row in rows:
        start = datetime.strptime(row.start_time, "%H:%M").time()
        end = datetime.strptime(row.end_time, "%H:%M").time()

        # Attendance allowed only from start time until strictly before end time.
        if start <= now_time < end:
            return "Present" if now_time == start else "Late"

    return None
