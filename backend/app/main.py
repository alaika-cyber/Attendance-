from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.bootstrap import apply_lightweight_sqlite_migrations
from app.db.session import engine
from app.services.monthly_report_scheduler import monthly_report_scheduler

from app import models  # noqa: F401

settings = get_settings()

app = FastAPI(title=settings.app_name)
_scheduler_task = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    global _scheduler_task
    apply_lightweight_sqlite_migrations(engine)
    Base.metadata.create_all(bind=engine)
    if settings.auto_monthly_reports_enabled and _scheduler_task is None:
        _scheduler_task = asyncio.create_task(monthly_report_scheduler())


app.include_router(api_router, prefix=settings.api_prefix)
