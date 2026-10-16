from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from models.location import Location
from schemas.location import LocationCreate, LocationUpdate


# Tipos de ubicación (valor crudo; el front los traduce). Para un tipo nuevo, agregarlo aquí.
LOCATION_TYPES = [
    "branch",       # sucursal
    "cedis",        # centro de distribución
    "corporate",    # corporativo
]


def _ensure_valid_type(location_type: str):
    if location_type not in LOCATION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de ubicación inválido. Usa uno de: {', '.join(LOCATION_TYPES)}"
        )


def get_locations(db: Session):
    return (
        db.query(Location)
        .order_by(Location.name.asc())
        .all()
    )


def get_location_by_id(db: Session, location_id: int):
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Ubicación no encontrada"
        )

    return location


def _ensure_unique_name(db: Session, name: str, exclude_id: int = None):
    query = db.query(Location).filter(func.lower(Location.name) == name.lower())

    if exclude_id is not None:
        query = query.filter(Location.id != exclude_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="La ubicación ya existe"
        )


def create_location(db: Session, location_data: LocationCreate):
    name = location_data.name.strip()
    _ensure_unique_name(db, name)
    _ensure_valid_type(location_data.type)

    location = Location(
        name=name,
        type=location_data.type,
        city=location_data.city,
        is_active=True
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


def update_location(db: Session, location_id: int, location_data: LocationUpdate):
    location = get_location_by_id(db, location_id)

    data = location_data.model_dump(exclude_unset=True)

    if "name" in data:
        data["name"] = data["name"].strip()
        _ensure_unique_name(db, data["name"], exclude_id=location_id)

    if "type" in data:
        _ensure_valid_type(data["type"])

    for field, value in data.items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)

    return location
