from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TicketCommentCreate(BaseModel):
    body: str = Field(..., min_length=1)
    is_internal: bool = False


class TicketCommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: Optional[int]
    body: str
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True