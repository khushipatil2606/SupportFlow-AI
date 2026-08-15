from pydantic import BaseModel


class TicketCreate(BaseModel):
    user_id: int
    issue: str
    priority: str = "Medium"


class TicketStatusUpdate(BaseModel):
    status: str


class TicketResponse(BaseModel):
    id: int
    user_id: int
    issue: str
    priority: str
    status: str

    class Config:
        from_attributes = True