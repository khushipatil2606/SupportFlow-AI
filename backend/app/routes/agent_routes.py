from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.routes.order_routes import get_db
from backend.app.services.agent_service import run_agent
from backend.app.services.ticket_tools import get_user_ticket_history


router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"]
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class AgentRequest(BaseModel):
    user_id: int
    message: str


class AgentResponse(BaseModel):
    response: str


# ============================================================
# AI CHAT
# ============================================================

@router.post(
    "/chat",
    response_model=AgentResponse
)
def agent_chat(
    request: AgentRequest,
    db: Session = Depends(get_db)
):

    response = run_agent(
        message=request.message,
        user_id=request.user_id,
        db=db
    )

    return {
        "response": response
    }


# ============================================================
# TICKET HISTORY
# ============================================================

@router.get("/tickets/{user_id}")
def ticket_history(
    user_id: int,
    db: Session = Depends(get_db)
):

    result = get_user_ticket_history(
        user_id=user_id,
        db=db
    )

    return result