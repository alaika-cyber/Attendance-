from datetime import datetime

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Student
from app.services.reports_service import get_student_attendance_stats

settings = get_settings()


RULES = {
    "attendance": "You can ask: 'what is my attendance percentage?'",
    "shortage": "You can ask: 'am I below 75% attendance?'",
}


def _rule_based_response(query: str, student_id: int, db: Session) -> str | None:
    q = query.lower()
    stats = get_student_attendance_stats(db, student_id)
    percentage = stats["attendance_percentage"]

    if "percentage" in q or "attendance" in q:
        return (
            f"Your attendance is {percentage:.1f}% "
            f"({stats['present_count']} present out of {stats['total_sessions']} sessions)."
        )

    if "shortage" in q or "below" in q:
        if percentage < 75:
            return "Alert: your attendance is below 75%. Please improve regularity."
        return "Good news: your attendance is above shortage threshold."

    return None


def generate_chatbot_response(query: str, student_id: int, db: Session) -> str:
    rule = _rule_based_response(query, student_id, db)
    if rule:
        return rule

    if not settings.openai_api_key:
        return f"I can answer attendance and shortage queries. {RULES['attendance']} {RULES['shortage']}"

    client = OpenAI(api_key=settings.openai_api_key)
    student_exists = db.query(Student.id).filter(Student.id == student_id).first()
    if not student_exists:
        return "Student account not found."

    completion = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are an attendance assistant. Give short, policy-safe, accurate answers. "
                    f"Current timestamp: {datetime.utcnow().isoformat()}"
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    return completion.output_text.strip() if completion.output_text else "No response generated."
