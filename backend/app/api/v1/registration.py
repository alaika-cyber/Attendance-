from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.student import StudentRegistrationRequest, StudentRegistrationResponse
from app.services.registration_service import register_student

router = APIRouter(prefix="/registration", tags=["registration"])


@router.post("/student", response_model=StudentRegistrationResponse)
def student_registration(
    payload: StudentRegistrationRequest,
    db: Session = Depends(get_db_session),
):
    student = register_student(
        db=db,
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        roll_no=payload.roll_no,
        class_code=payload.class_code,
        class_name=payload.class_name,
        academic_year=payload.academic_year,
        live_image_b64=payload.live_image_b64,
    )
    return StudentRegistrationResponse(student_id=student.id, status="pending_admin_approval")
