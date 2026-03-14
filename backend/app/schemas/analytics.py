from pydantic import BaseModel


class TopStudent(BaseModel):
    student_id: int
    full_name: str
    roll_no: str
    classroom_id: int
    class_code: str
    present_count: int
    total_sessions: int
    attendance_percentage: float


class SpoofSummary(BaseModel):
    total_attempts: int


class DashboardResponse(BaseModel):
    top_students: list[TopStudent]
    spoof_summary: SpoofSummary


class ClassWiseAttendanceRow(BaseModel):
    student_id: int
    full_name: str
    roll_no: str
    classroom_id: int
    class_code: str
    class_name: str
    present_count: int
    total_sessions: int
    attendance_percentage: float


class SpoofReportRow(BaseModel):
    event_id: int
    student_id: int | None
    student_name: str | None
    roll_no: str | None
    class_code: str | None
    class_name: str | None
    spoof_type: str
    reason: str
    timestamp: str


class StudentAttendanceSummary(BaseModel):
    student_id: int
    present_count: int
    total_sessions: int
    attendance_percentage: float
    shortage: bool


class MonthlyEmailReportResponse(BaseModel):
    month: str
    student_emails_sent: int
    admin_emails_sent: int
