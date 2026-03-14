from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User, UserRole


def run() -> None:
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == "admin@attendance.local").first()
        if exists:
            print("Admin already exists")
            return

        admin = User(
            email="admin@attendance.local",
            password_hash=hash_password("admin1234"),
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Admin created: admin@attendance.local / admin1234")
    finally:
        db.close()


if __name__ == "__main__":
    run()
