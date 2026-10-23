from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Mismo límite que MAX_TEXT en el front (utils/labels.js)
MAX_TEXT = 10000


class TicketCreate(BaseModel):
    incidencia_id: int = Field(..., gt=0)
    subincidencia_id: int = Field(..., gt=0)
    description: str = Field(..., min_length=5, max_length=MAX_TEXT)


# El estado NO se cambia aquí: va por /status, /close o /cancel (respetan el flujo)
class TicketUpdate(BaseModel):
    incidencia_id: Optional[int] = Field(None, gt=0)
    subincidencia_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=5, max_length=MAX_TEXT)
    priority: Optional[str] = None


class TicketAssign(BaseModel):
    assigned_to_user_id: int = Field(..., gt=0)


class TicketSurveyResponse(BaseModel):
    rating: int
    comment: Optional[str]
    is_auto: bool
    created_at: Optional[datetime]


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

    location_id: Optional[int] = None
    location_name: Optional[str] = None

    description: str


    status: str
    priority: str

    created_at: datetime
    updated_at: Optional[datetime]

    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None

    # "confirm" | "survey" | None: lo que le falta responder al solicitante
    feedback_state: Optional[str] = None
    feedback_due_at: Optional[datetime] = None
    survey: Optional[TicketSurveyResponse] = None


class TicketPage(BaseModel):
    items: list[TicketResponse]
    total: int
    page: int
    page_size: int
    status_counts: dict[str, int]


class TicketStatusUpdate(BaseModel):
    status: str


class TicketCancel(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000)


class TicketSurveyCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class TicketReopen(BaseModel):
    reason: str = Field(..., min_length=5, max_length=2000)
