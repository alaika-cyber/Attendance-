from app.models.attendance import Attendance
from app.models.campus_geofence import CampusGeofence
from app.models.classroom import Classroom
from app.models.face_embedding import FaceEmbedding
from app.models.notification import Notification
from app.models.spoof_event import SpoofEvent
from app.models.student import ApprovalStatus, Student
from app.models.user import User, UserRole
from app.models.weekly_schedule import WeeklySchedule

__all__ = [
    "Attendance",
    "CampusGeofence",
    "Classroom",
    "FaceEmbedding",
    "Notification",
    "SpoofEvent",
    "ApprovalStatus",
    "Student",
    "User",
    "UserRole",
    "WeeklySchedule",
]
