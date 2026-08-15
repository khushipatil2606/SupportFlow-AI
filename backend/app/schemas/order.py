from pydantic import BaseModel


class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    total_amount: float


class OrderStatusUpdate(BaseModel):
    status: str


class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    status: str
    total_amount: float

    class Config:
        from_attributes = True


class OrderCancelRequest(BaseModel):
    confirmation: bool