from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SpoofEvent(Base):
    __tablename__ = "spoof_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    spoof_type: Mapped[str] = mapped_column(String(64), default="unknown")
    reason: Mapped[str] = mapped_column(String(255))
    alert_status: Mapped[str] = mapped_column(String(32), default="new")
    evidence_image_b64: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
