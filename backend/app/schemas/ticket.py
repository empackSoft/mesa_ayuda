from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    incidencia_id: int = Field(..., gt=0)
    subincidencia_id: int = Field(..., gt=0)
    description: str = Field(..., min_length=5)
    attachment_path: Optional[str] = None


class TicketUpdate(BaseModel):
    incidencia_id: Optional[int] = Field(None, gt=0)
    subincidencia_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=5)
    attachment_path: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TicketAssign(BaseModel):
    assigned_to_user_id: int = Field(..., gt=0)


class TicketResponse(BaseModel):
    id: int

    incidencia_id: int
    incidencia: str

    subincidencia_id: int
    subincidencia: str

    created_by_user_id: Optional[int]
    created_by_user_name: Optional[str]

    assigned_to_user_id: Optional[int]
    assigned_to_user_name: Optional[str]

    description: str
    attachment_path: Optional[str]

    status: str
    priority: str

    created_at: datetime
    updated_at: Optional[datetime]


class TicketStatusUpdate(BaseModel):
    status: str