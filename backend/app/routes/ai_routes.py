from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.gemini_service import ask_gemini


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


class AIRequest(BaseModel):
    message: str


class AIResponse(BaseModel):
    response: str


@router.post(
    "/chat",
    response_model=AIResponse
)
def chat_with_ai(
    request: AIRequest
):

    response = ask_gemini(
        request.message
    )

    return {
        "response": response
    }