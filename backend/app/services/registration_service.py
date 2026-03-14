from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import ApprovalStatus, Classroom, FaceEmbedding, Student, User, UserRole
from app.services.face_service import generate_embedding


def register_student(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    roll_no: str,
    class_code: str,
    class_name: str,
    academic_year: str,
    live_image_b64: str,
) -> Student:
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    existing_roll = db.query(Student).filter(Student.roll_no == roll_no).first()
    if existing_roll:
        raise HTTPException(status_code=409, detail="Roll number already registered")

    classroom = db.query(Classroom).filter(Classroom.code == class_code).first()
    if not classroom:
        classroom = Classroom(code=class_code, name=class_name, academic_year=academic_year)
        db.add(classroom)
        db.flush()

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=UserRole.STUDENT,
    )
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        roll_no=roll_no,
        classroom_id=classroom.id,
        captured_image_b64=live_image_b64,
        approval_status=ApprovalStatus.PENDING,
        is_approved=False,
    )
    db.add(student)
    db.flush()

    embedding = FaceEmbedding(student_id=student.id, embedding=generate_embedding(live_image_b64))
    db.add(embedding)
    db.commit()
    db.refresh(student)
    return student
