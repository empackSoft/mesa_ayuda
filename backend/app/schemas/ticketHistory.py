from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TicketHistoryResponse(BaseModel):
    id: int
    ticket_id: int

    user_id: Optional[int]
    user_name: Optional[str]
    user_role: Optional[str]

    action: str
    message:str

    old_value: Optional[str]
    new_value: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True