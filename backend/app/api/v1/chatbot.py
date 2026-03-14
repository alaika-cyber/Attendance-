from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_student, get_db_session
from app.schemas.chatbot import ChatbotRequest, ChatbotResponse
from app.services.chatbot_service import generate_chatbot_response

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/query", response_model=ChatbotResponse)
def query_chatbot(
    payload: ChatbotRequest,
    student=Depends(get_current_student),
    db: Session = Depends(get_db_session),
):
    answer = generate_chatbot_response(payload.query, student.id, db)
    return ChatbotResponse(answer=answer)
