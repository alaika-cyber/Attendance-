from sqlalchemy import Engine


def _sqlite_table_exists(engine: Engine, table_name: str) -> bool:
    with engine.connect() as conn:
        row = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:name",
            {"name": table_name},
        ).first()
        return row is not None


def _sqlite_columns(engine: Engine, table_name: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row[1]) for row in rows}


def apply_lightweight_sqlite_migrations(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as conn:
        if _sqlite_table_exists(engine, "students"):
            student_columns = _sqlite_columns(engine, "students")
            if "captured_image_b64" not in student_columns:
                conn.exec_driver_sql("ALTER TABLE students ADD COLUMN captured_image_b64 TEXT NOT NULL DEFAULT ''")
            if "approval_status" not in student_columns:
                conn.exec_driver_sql(
                    "ALTER TABLE students ADD COLUMN approval_status VARCHAR(16) NOT NULL DEFAULT 'pending'"
                )
            if "approval_decided_at" not in student_columns:
                conn.exec_driver_sql("ALTER TABLE students ADD COLUMN approval_decided_at DATETIME")
            if "approval_reason" not in student_columns:
                conn.exec_driver_sql("ALTER TABLE students ADD COLUMN approval_reason VARCHAR(255)")

            conn.exec_driver_sql(
                "UPDATE students SET approval_status='approved' WHERE is_approved=1 AND approval_status='pending'"
            )

        if _sqlite_table_exists(engine, "spoof_events"):
            spoof_columns = _sqlite_columns(engine, "spoof_events")
            if "spoof_type" not in spoof_columns:
                conn.exec_driver_sql(
                    "ALTER TABLE spoof_events ADD COLUMN spoof_type VARCHAR(64) NOT NULL DEFAULT 'unknown'"
                )
            if "alert_status" not in spoof_columns:
                conn.exec_driver_sql(
                    "ALTER TABLE spoof_events ADD COLUMN alert_status VARCHAR(32) NOT NULL DEFAULT 'new'"
                )

        if _sqlite_table_exists(engine, "attendance"):
            conn.exec_driver_sql("UPDATE attendance SET status='Present' WHERE status='present'")
            conn.exec_driver_sql("UPDATE attendance SET status='Late' WHERE status='late'")
            conn.exec_driver_sql("UPDATE attendance SET status='Absent' WHERE status='absent'")

        if _sqlite_table_exists(engine, "notifications"):
            notification_columns = _sqlite_columns(engine, "notifications")
            if "severity" not in notification_columns:
                conn.exec_driver_sql(
                    "ALTER TABLE notifications ADD COLUMN severity VARCHAR(16) NOT NULL DEFAULT 'info'"
                )
            if "metadata_json" not in notification_columns:
                conn.exec_driver_sql("ALTER TABLE notifications ADD COLUMN metadata_json TEXT")
