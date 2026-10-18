from pydantic import BaseModel, Field
from typing import Optional


class NotifyGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    emails: Optional[list[str]] = None


class NotifyGroupResponse(BaseModel):
    id: int
    key: str
    name: str
    emails: list[str]

    class Config:
        from_attributes = True
