from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Attendance, SpoofEvent, Student, User


def top_regular_students(db: Session, classroom_id: int | None = None, limit: int = 10):
    query = (
        db.query(
            Student.id.label("student_id"),
            User.full_name.label("full_name"),
            Student.roll_no.label("roll_no"),
            func.count(Attendance.id).label("present_count"),
        )
        .join(User, User.id == Student.user_id)
        .join(Attendance, Attendance.student_id == Student.id)
        .group_by(Student.id, User.full_name, Student.roll_no)
        .order_by(func.count(Attendance.id).desc())
        .limit(limit)
    )

    if classroom_id:
        query = query.filter(Attendance.classroom_id == classroom_id)

    return query.all()


def spoof_attempt_count(db: Session, classroom_id: int | None = None) -> int:
    query = db.query(func.count(SpoofEvent.id))
    if classroom_id:
        query = query.filter(SpoofEvent.classroom_id == classroom_id)
    return int(query.scalar() or 0)
