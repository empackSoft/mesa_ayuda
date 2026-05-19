from pydantic import BaseModel

class TicketCreate(BaseModel):
    title: str
    status: str
    priority: str


class TicketResponse(BaseModel):
    id: int
    title: str
    status: str
    priority: str

    class Config:
        from_attributes = True