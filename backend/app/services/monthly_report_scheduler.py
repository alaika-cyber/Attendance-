import asyncio
from datetime import datetime, timedelta

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.reports_service import send_monthly_reports

settings = get_settings()
_last_sent_month: str | None = None


def _target_month_for_report(now: datetime) -> str:
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_last_day = first_of_month - timedelta(days=1)
    return prev_month_last_day.strftime("%Y-%m")


async def monthly_report_scheduler() -> None:
    global _last_sent_month

    while True:
        now = datetime.utcnow()
        target_month = _target_month_for_report(now)

        should_send = (
            now.day == 1
            and now.hour >= settings.monthly_report_run_hour_utc
            and _last_sent_month != target_month
        )

        if should_send:
            db = SessionLocal()
            try:
                send_monthly_reports(db, month=target_month)
                _last_sent_month = target_month
            finally:
                db.close()

        await asyncio.sleep(3600)
