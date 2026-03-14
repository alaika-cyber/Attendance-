from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_student, get_db_session, require_admin
from app.schemas.analytics import (
    ClassWiseAttendanceRow,
    DashboardResponse,
    MonthlyEmailReportResponse,
    SpoofReportRow,
    SpoofSummary,
    StudentAttendanceSummary,
    TopStudent,
)
from app.services.analytics_service import spoof_attempt_count
from app.services.reports_service import (
    class_wise_attendance_report,
    get_student_attendance_stats,
    send_monthly_reports,
    spoof_attempt_report,
    top_regular_students_by_percentage,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    classroom_id: int | None = None,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    top = top_regular_students_by_percentage(db, classroom_id=classroom_id)
    spoof_count = spoof_attempt_count(db, classroom_id=classroom_id)

    return DashboardResponse(
        top_students=[
            TopStudent(
                student_id=row.student_id,
                full_name=row.full_name,
                roll_no=row.roll_no,
                classroom_id=row.classroom_id,
                class_code=row.class_code,
                present_count=row.present_count,
                total_sessions=row.total_sessions,
                attendance_percentage=row.attendance_percentage,
            )
            for row in top
        ],
        spoof_summary=SpoofSummary(total_attempts=spoof_count),
    )


@router.get("/top-regular", response_model=list[TopStudent])
def top_regular(
    classroom_id: int | None = None,
    limit: int = 10,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    rows = top_regular_students_by_percentage(db, classroom_id=classroom_id, limit=limit)
    return [
        TopStudent(
            student_id=row["student_id"],
            full_name=row["full_name"],
            roll_no=row["roll_no"],
            classroom_id=row["classroom_id"],
            class_code=row["class_code"],
            present_count=row["present_count"],
            total_sessions=row["total_sessions"],
            attendance_percentage=row["attendance_percentage"],
        )
        for row in rows
    ]


@router.get("/class-wise", response_model=list[ClassWiseAttendanceRow])
def class_wise(
    classroom_id: int,
    month: str | None = None,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    rows = class_wise_attendance_report(db, classroom_id=classroom_id, month=month)
    return [ClassWiseAttendanceRow(**row) for row in rows]


@router.get("/spoof-report", response_model=list[SpoofReportRow])
def spoof_report(
    classroom_id: int | None = None,
    month: str | None = None,
    limit: int = 100,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    rows = spoof_attempt_report(db, classroom_id=classroom_id, month=month, limit=limit)
    return [SpoofReportRow(**row) for row in rows]


@router.get("/student-summary", response_model=StudentAttendanceSummary)
def student_summary(
    month: str | None = None,
    student=Depends(get_current_student),
    db: Session = Depends(get_db_session),
):
    stats = get_student_attendance_stats(db, student.id, month=month)
    return StudentAttendanceSummary(
        student_id=student.id,
        present_count=stats["present_count"],
        total_sessions=stats["total_sessions"],
        attendance_percentage=stats["attendance_percentage"],
        shortage=stats["attendance_percentage"] < 75.0,
    )


@router.post("/monthly-email-report", response_model=MonthlyEmailReportResponse)
def monthly_email_report(
    month: str | None = None,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db_session),
):
    result = send_monthly_reports(db, month=month)
    return MonthlyEmailReportResponse(**result)
