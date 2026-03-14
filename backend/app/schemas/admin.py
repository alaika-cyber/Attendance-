from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    student_id: int
    approve: bool
    reason: str | None = None


class PendingApprovalItem(BaseModel):
    student_id: int
    full_name: str
    email: str
    roll_no: str
    class_code: str
    class_name: str
    academic_year: str
    captured_image_b64: str


class ApprovalResponse(BaseModel):
    student_id: int
    status: str
    email_notification_sent: bool


class GeofenceUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float


class GeofenceResponse(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float


class SpoofAlertItem(BaseModel):
    event_id: int
    student_id: int | None
    student_name: str | None
    roll_no: str | None
    class_code: str | None
    class_name: str | None
    spoof_type: str
    reason: str
    alert_status: str
    timestamp: str
    evidence_image_b64: str


class TimetableCreateRequest(BaseModel):
    subject_name: str
    class_code: str
    class_name: str | None = None
    academic_year: str | None = None
    schedule_date: str
    start_time: str
    end_time: str


class TimetableItem(BaseModel):
    schedule_id: int
    subject_name: str
    class_code: str
    class_name: str
    academic_year: str
    schedule_date: str
    start_time: str
    end_time: str
