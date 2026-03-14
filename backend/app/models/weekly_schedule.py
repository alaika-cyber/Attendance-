from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeeklySchedule(Base):
    __tablename__ = "weekly_schedules"
    __table_args__ = (
        UniqueConstraint(
            "classroom_id",
            "schedule_date",
            "start_time",
            "end_time",
            "subject_name",
            name="uq_weekly_schedule_slot",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"), index=True)
    subject_name: Mapped[str] = mapped_column(String(255), index=True)
    schedule_date: Mapped[str] = mapped_column(String(10), index=True)
    start_time: Mapped[str] = mapped_column(String(5))
    end_time: Mapped[str] = mapped_column(String(5))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
