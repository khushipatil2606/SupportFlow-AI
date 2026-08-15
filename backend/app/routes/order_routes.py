from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.connection import SessionLocal
from backend.app.models.order import Order
from backend.app.models.user import User
from backend.app.models.product import Product

from backend.app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderCancelRequest
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# ============================================================
# DATABASE
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# CREATE ORDER
# ============================================================

@router.post(
    "/",
    response_model=OrderResponse
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):

    # Check if user exists

    user = (
        db.query(User)
        .filter(User.id == order_data.user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    # Check if product exists

    product = (
        db.query(Product)
        .filter(Product.id == order_data.product_id)
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    # Check stock

    if product.stock <= 0:

        raise HTTPException(
            status_code=400,
            detail="Product is out of stock"
        )


    # Create order

    order = Order(
        user_id=order_data.user_id,
        product_id=order_data.product_id,
        total_amount=order_data.total_amount,
        status="Processing"
    )


    # Reduce product stock

    product.stock -= 1


    db.add(order)

    db.commit()

    db.refresh(order)


    return order


# ============================================================
# GET ALL ORDERS
# ============================================================

@router.get(
    "/",
    response_model=list[OrderResponse]
)
def get_orders(
    db: Session = Depends(get_db)
):

    orders = (
        db.query(Order)
        .all()
    )

    return orders


# ============================================================
# GET ORDERS FOR SPECIFIC USER
# ============================================================

@router.get(
    "/user/{user_id}",
    response_model=list[OrderResponse]
)
def get_user_orders(
    user_id: int,
    db: Session = Depends(get_db)
):

    # Check if user exists

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail=f"User #{user_id} was not found."
        )


    # Get user's orders

    orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.id.desc())
        .all()
    )


    return orders


# ============================================================
# GET SINGLE ORDER
# ============================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    return order


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse
)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db)
):

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    allowed_statuses = [
        "Processing",
        "Shipped",
        "Delivered",
        "Cancelled",
        "Refunded"
    ]


    if status_data.status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )


    order.status = status_data.status


    db.commit()

    db.refresh(order)


    return order


# ============================================================
# CANCEL ORDER
# ============================================================

@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse
)
def cancel_order(
    order_id: int,
    request: OrderCancelRequest,
    db: Session = Depends(get_db)
):

    # Find order

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )


    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )


    # Delivered orders cannot be cancelled

    if order.status == "Delivered":

        raise HTTPException(
            status_code=400,
            detail="Delivered orders cannot be cancelled"
        )


    # Already cancelled

    if order.status == "Cancelled":

        raise HTTPException(
            status_code=400,
            detail="Order is already cancelled"
        )


    # Confirmation required

    if not request.confirmation:

        raise HTTPException(
            status_code=400,
            detail="Cancellation requires confirmation"
        )


    # Cancel order

    order.status = "Cancelled"


    db.commit()

    db.refresh(order)


    return order