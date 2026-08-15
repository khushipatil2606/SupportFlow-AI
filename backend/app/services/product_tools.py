from sqlalchemy.orm import Session

from backend.app.models.product import Product


def get_product_details(
    product_id: int,
    db: Session
) -> dict:

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        return {
            "success": False,
            "message": f"Product #{product_id} was not found."
        }

    return {
        "success": True,
        "product_id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock
    }