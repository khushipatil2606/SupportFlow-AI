from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.connection import SessionLocal
from backend.app.models.ticket import SupportTicket
from backend.app.models.user import User

from backend.app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate
)


router = APIRouter(
    prefix="/tickets",
    tags=["Support Tickets"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# CREATE SUPPORT TICKET
# --------------------------------------------------

@router.post("/", response_model=TicketResponse)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):

    # Check if user exists
    user = (
        db.query(User)
        .filter(User.id == ticket_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    allowed_priorities = [
        "Low",
        "Medium",
        "High",
        "Critical"
    ]

    if ticket_data.priority not in allowed_priorities:
        raise HTTPException(
            status_code=400,
            detail="Invalid priority"
        )

    ticket = SupportTicket(
        user_id=ticket_data.user_id,
        issue=ticket_data.issue,
        priority=ticket_data.priority,
        status="Open"
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


# --------------------------------------------------
# GET ALL TICKETS
# --------------------------------------------------

@router.get("/", response_model=list[TicketResponse])
def get_tickets(
    db: Session = Depends(get_db)
):

    tickets = (
        db.query(SupportTicket)
        .all()
    )

    return tickets


# --------------------------------------------------
# GET SINGLE TICKET
# --------------------------------------------------

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):

    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found"
        )

    return ticket


# --------------------------------------------------
# UPDATE TICKET STATUS
# --------------------------------------------------

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse
)
def update_ticket_status(
    ticket_id: int,
    status_data: TicketStatusUpdate,
    db: Session = Depends(get_db)
):

    ticket = (
        db.query(SupportTicket)
        .filter(SupportTicket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found"
        )

    allowed_statuses = [
        "Open",
        "In Progress",
        "Resolved",
        "Closed"
    ]

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid ticket status"
        )

    ticket.status = status_data.status

    db.commit()
    db.refresh(ticket)

    return ticket