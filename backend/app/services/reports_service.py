from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Attendance, Classroom, SpoofEvent, Student, User, UserRole
from app.services.email_service import send_email
from app.services.notification_service import notify_monthly_report_admin


def _month_filter(query, month: str | None):
    if month:
        return query.filter(Attendance.session_date.like(f"{month}%"))
    return query


def get_total_sessions_for_class(db: Session, classroom_id: int, month: str | None = None) -> int:
    query = db.query(func.count(func.distinct(Attendance.session_date))).filter(
        Attendance.classroom_id == classroom_id
    )
    if month:
        query = query.filter(Attendance.session_date.like(f"{month}%"))
    return int(query.scalar() or 0)


def get_student_attendance_stats(db: Session, student_id: int, month: str | None = None) -> dict:
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return {
            "present_count": 0,
            "total_sessions": 0,
            "attendance_percentage": 0.0,
        }

    present_query = db.query(func.count(Attendance.id)).filter(
        Attendance.student_id == student.id,
        Attendance.status.in_(["Present", "Late", "present", "late"]),
    )
    if month:
        present_query = present_query.filter(Attendance.session_date.like(f"{month}%"))
    present_count = int(present_query.scalar() or 0)

    total_sessions = get_total_sessions_for_class(db, student.classroom_id, month=month)
    percentage = (present_count / total_sessions * 100.0) if total_sessions > 0 else 0.0

    return {
        "present_count": present_count,
        "total_sessions": total_sessions,
        "attendance_percentage": round(percentage, 2),
    }


def top_regular_students_by_percentage(
    db: Session, classroom_id: int | None = None, limit: int = 10
) -> list[dict]:
    students_query = db.query(Student, User, Classroom).join(User, User.id == Student.user_id).join(
        Classroom, Classroom.id == Student.classroom_id
    )
    if classroom_id:
        students_query = students_query.filter(Student.classroom_id == classroom_id)

    rows = students_query.all()
    ranked: list[dict] = []
    for student, user, classroom in rows:
        stats = get_student_attendance_stats(db, student.id)
        ranked.append(
            {
                "student_id": student.id,
                "full_name": user.full_name,
                "roll_no": student.roll_no,
                "classroom_id": classroom.id,
                "class_code": classroom.code,
                "present_count": stats["present_count"],
                "total_sessions": stats["total_sessions"],
                "attendance_percentage": stats["attendance_percentage"],
            }
        )

    ranked.sort(key=lambda item: item["attendance_percentage"], reverse=True)
    return ranked[: max(1, min(limit, 100))]


def class_wise_attendance_report(
    db: Session, classroom_id: int, month: str | None = None
) -> list[dict]:
    students = (
        db.query(Student, User, Classroom)
        .join(User, User.id == Student.user_id)
        .join(Classroom, Classroom.id == Student.classroom_id)
        .filter(Student.classroom_id == classroom_id)
        .all()
    )

    report: list[dict] = []
    for student, user, classroom in students:
        stats = get_student_attendance_stats(db, student.id, month=month)
        report.append(
            {
                "student_id": student.id,
                "full_name": user.full_name,
                "roll_no": student.roll_no,
                "classroom_id": classroom.id,
                "class_code": classroom.code,
                "class_name": classroom.name,
                "present_count": stats["present_count"],
                "total_sessions": stats["total_sessions"],
                "attendance_percentage": stats["attendance_percentage"],
            }
        )

    report.sort(key=lambda item: item["roll_no"])
    return report


def spoof_attempt_report(
    db: Session, classroom_id: int | None = None, month: str | None = None, limit: int = 100
) -> list[dict]:
    query = (
        db.query(SpoofEvent, Student, User, Classroom)
        .outerjoin(Student, Student.id == SpoofEvent.student_id)
        .outerjoin(User, User.id == Student.user_id)
        .outerjoin(Classroom, Classroom.id == SpoofEvent.classroom_id)
    )

    if classroom_id:
        query = query.filter(SpoofEvent.classroom_id == classroom_id)
    if month:
        query = query.filter(func.strftime("%Y-%m", SpoofEvent.created_at) == month)

    rows = query.order_by(SpoofEvent.created_at.desc()).limit(max(1, min(limit, 500))).all()
    return [
        {
            "event_id": event.id,
            "student_id": event.student_id,
            "student_name": user.full_name if user else None,
            "roll_no": student.roll_no if student else None,
            "class_code": classroom.code if classroom else None,
            "class_name": classroom.name if classroom else None,
            "spoof_type": event.spoof_type,
            "reason": event.reason,
            "timestamp": event.created_at.isoformat(),
        }
        for event, student, user, classroom in rows
    ]


def send_monthly_reports(db: Session, month: str | None = None) -> dict:
    target_month = month or datetime.utcnow().strftime("%Y-%m")

    students = (
        db.query(Student, User, Classroom)
        .join(User, User.id == Student.user_id)
        .join(Classroom, Classroom.id == Student.classroom_id)
        .all()
    )

    student_emails_sent = 0
    for student, user, classroom in students:
        stats = get_student_attendance_stats(db, student.id, month=target_month)
        body = (
            f"Hello {user.full_name},\n\n"
            f"Monthly Attendance Report ({target_month})\n"
            f"Class: {classroom.name} ({classroom.code})\n"
            f"Present Sessions: {stats['present_count']}\n"
            f"Total Class Sessions: {stats['total_sessions']}\n"
            f"Attendance Percentage: {stats['attendance_percentage']:.2f}%\n"
        )
        ok = send_email(
            to_email=user.email,
            subject=f"Monthly Attendance Report - {target_month}",
            body=body,
        )
        if ok:
            student_emails_sent += 1

    admin_users = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).all()
    top_students = top_regular_students_by_percentage(db, limit=10)
    spoof_count = len(spoof_attempt_report(db, month=target_month, limit=500))

    admin_body = [
        f"Monthly Attendance Admin Report ({target_month})",
        "",
        f"Total Student Emails Sent: {student_emails_sent}",
        f"Total Spoof Attempts: {spoof_count}",
        "",
        "Top Regular Students:",
    ]
    for idx, student in enumerate(top_students, start=1):
        admin_body.append(
            f"{idx}. {student['full_name']} ({student['roll_no']}) - {student['attendance_percentage']:.2f}%"
        )

    admin_emails_sent = 0
    for admin in admin_users:
        ok = send_email(
            to_email=admin.email,
            subject=f"Admin Monthly Attendance Report - {target_month}",
            body="\n".join(admin_body),
        )
        if ok:
            admin_emails_sent += 1

    result = {
        "month": target_month,
        "student_emails_sent": student_emails_sent,
        "admin_emails_sent": admin_emails_sent,
    }
    notify_monthly_report_admin(
        db,
        month=target_month,
        student_emails=student_emails_sent,
        admin_emails=admin_emails_sent,
    )
    db.commit()
    return result
