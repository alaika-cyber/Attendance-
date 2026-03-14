from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import ApprovalStatus, Student, User, UserRole

security = HTTPBearer(auto_error=False)


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing auth token")

    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    user = db.query(User).filter(User.id == int(user_id), User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def get_current_student(
    user: User = Depends(get_current_user), db: Session = Depends(get_db_session)
) -> Student:
    student = db.query(Student).filter(Student.user_id == user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile missing")
    if student.approval_status == ApprovalStatus.REJECTED:
        raise HTTPException(status_code=403, detail="Student registration was rejected by admin")
    if student.approval_status != ApprovalStatus.APPROVED or not student.is_approved:
        raise HTTPException(status_code=403, detail="Student registration pending admin approval")
    return student
