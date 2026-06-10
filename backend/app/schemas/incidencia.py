from pydantic import BaseModel, Field
from typing import Optional


class IncidenciaCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class IncidenciaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


class IncidenciaResponse(BaseModel):
    id: int
    name: str
    is_active: bool

    class Config:
        from_attributes = True