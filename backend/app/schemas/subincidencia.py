from pydantic import BaseModel, Field
from typing import Optional


class SubincidenciaCreate(BaseModel):
    incidencia_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=100)


class SubincidenciaUpdate(BaseModel):
    incidencia_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None


class SubincidenciaResponse(BaseModel):
    id: int
    incidencia_id: int
    name: str
    is_active: bool

    class Config:
        from_attributes = True