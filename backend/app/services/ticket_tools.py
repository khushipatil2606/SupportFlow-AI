from sqlalchemy.orm import Session

from backend.app.models.ticket import SupportTicket
from backend.app.models.user import User


# ============================================================
# CREATE SUPPORT TICKET
# ============================================================

def create_support_ticket(
    user_id: int,
    issue: str,
    priority: str,
    db: Session
) -> dict:

    # ==========================================
    # CHECK USER
    # ==========================================

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return {
            "success": False,
            "message": f"User #{user_id} was not found."
        }

    # ==========================================
    # NORMALIZE PRIORITY
    # ==========================================

    priority = priority.strip().capitalize()

    allowed_priorities = {
        "Low",
        "Medium",
        "High",
        "Critical"
    }

    if priority not in allowed_priorities:
        priority = "Medium"

    # ==========================================
    # AUTOMATIC PRIORITY DETECTION
    # ==========================================

    issue_lower = issue.lower()

    critical_keywords = [
        "safety",
        "dangerous",
        "fire",
        "explosion",
        "electric shock",
        "security breach",
        "hacked",
        "fraud"
    ]

    high_keywords = [
        "damaged",
        "broken",
        "urgent",
        "serious",
        "not working",
        "doesn't work",
        "does not work",
        "defective",
        "wrong product",
        "missing",
        "leaking"
    ]

    if any(keyword in issue_lower for keyword in critical_keywords):

        priority = "Critical"

    elif any(keyword in issue_lower for keyword in high_keywords):

        priority = "High"

    # ==========================================
    # CREATE TICKET
    # ==========================================

    ticket = SupportTicket(
        user_id=user_id,
        issue=issue,
        priority=priority,
        status="Open"
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # ==========================================
    # RETURN RESPONSE
    # ==========================================

    return {
        "success": True,
        "ticket_id": ticket.id,
        "user_id": ticket.user_id,
        "issue": ticket.issue,
        "priority": ticket.priority,
        "status": ticket.status
    }


# ============================================================
# GET USER TICKET HISTORY
# ============================================================

def get_user_ticket_history(
    user_id: int,
    db: Session
) -> dict:

    # ==========================================
    # CHECK USER
    # ==========================================

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return {
            "success": False,
            "message": f"User #{user_id} was not found."
        }

    # ==========================================
    # GET TICKETS
    # ==========================================

    tickets = (
        db.query(SupportTicket)
        .filter(SupportTicket.user_id == user_id)
        .order_by(SupportTicket.id.desc())
        .all()
    )

    # ==========================================
    # FORMAT TICKETS
    # ==========================================

    ticket_list = []

    for ticket in tickets:

        ticket_list.append({
            "ticket_id": ticket.id,
            "issue": ticket.issue,
            "priority": ticket.priority,
            "status": ticket.status
        })

    # ==========================================
    # RETURN HISTORY
    # ==========================================

    return {
        "success": True,
        "user_id": user_id,
        "total_tickets": len(ticket_list),
        "tickets": ticket_list
    }