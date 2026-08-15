from sqlalchemy.orm import Session

from backend.app.models.order import Order


def cancel_order(
    order_id: int,
    db: Session
) -> dict:

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

    if order.status == "Delivered":
        return {
            "success": False,
            "message": "Delivered orders cannot be cancelled."
        }

    if order.status == "Cancelled":
        return {
            "success": False,
            "message": "This order is already cancelled."
        }

    order.status = "Cancelled"

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "order_id": order.id,
        "status": order.status,
        "message": f"Order #{order.id} has been cancelled successfully."
    }