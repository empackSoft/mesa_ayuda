from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TicketAttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    file_path: str
    original_name: Optional[str]
    uploaded_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True