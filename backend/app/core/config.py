from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Attendance Framework"
    env: str = "development"
    api_prefix: str = "/api/v1"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite:///./attendance.db"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_sender: str = ""
    smtp_use_tls: bool = True
    auto_monthly_reports_enabled: bool = False
    monthly_report_run_hour_utc: int = 8
    low_attendance_threshold_percent: float = 75.0
    suspicious_spoof_attempts_24h: int = 3

    geofence_lat: float = 12.9716
    geofence_lon: float = 77.5946
    geofence_radius_meters: float = 300.0

    max_spoof_score: float = 0.6

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

@lru_cache
def get_settings() -> Settings:
    return Settings()
