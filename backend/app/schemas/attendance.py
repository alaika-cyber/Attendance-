from pydantic import BaseModel


class AttendanceMarkRequest(BaseModel):
    class_code: str
    session_date: str
    latitude: float
    longitude: float
    live_image_b64: str


class AttendanceMarkResponse(BaseModel):
    attendance_id: int
    status: str
