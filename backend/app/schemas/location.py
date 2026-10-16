from pydantic import BaseModel, Field
from typing import Optional


class LocationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    type: str = Field(default="branch")
    city: Optional[str] = Field(None, max_length=100)


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    type: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class LocationResponse(BaseModel):
    id: int
    name: str
    type: str
    city: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
