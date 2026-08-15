from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import SessionLocal
from backend.app.models.product import Product
from backend.app.schemas.product import (
    ProductCreate,
    ProductResponse
)


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):

    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/", response_model=list[ProductResponse])
def get_products(
    db: Session = Depends(get_db)
):

    products = db.query(Product).all()

    return products