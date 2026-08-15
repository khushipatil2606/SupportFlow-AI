from sqlalchemy.orm import Session

from backend.app.models.order import Order


def get_order_status(
    order_id: int,
    db: Session
) -> dict:
    """
    Get the current status of a customer order.

    Args:
        order_id: The ID of the order to check.
        db: Database session.

    Returns:
        A dictionary containing order information.
    """

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        return {
            "success": False,
            "message": f"Order #{order_id} was not found."
        }

    return {
        "success": True,
        "order_id": order.id,
        "status": order.status,
        "total_amount": order.total_amount
    }