from pydantic import BaseModel, EmailStr


class StudentRegistrationRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    roll_no: str
    class_code: str
    class_name: str
    academic_year: str
    live_image_b64: str


class StudentRegistrationResponse(BaseModel):
    student_id: int
    status: str
