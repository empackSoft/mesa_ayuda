from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationResponse(BaseModel):
    id: int
    ticket_id: Optional[int]
    kind: str
    title: str
    body: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    unread_count: int
    items: list[NotificationResponse]
