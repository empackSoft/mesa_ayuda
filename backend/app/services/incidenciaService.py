from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.incidencia import Incidencia
from models.subincidencia import Subincidencia

from schemas.incidencia import IncidenciaCreate, IncidenciaUpdate
from schemas.subincidencia import SubincidenciaCreate, SubincidenciaUpdate


def get_incidencias(db: Session):
    return (
        db.query(Incidencia)
        .order_by(Incidencia.name.asc())
        .all()
    )


def get_active_incidencias(db: Session):
    return (
        db.query(Incidencia)
        .filter(Incidencia.is_active == True)
        .order_by(Incidencia.name.asc())
        .all()
    )


def get_incidencia_by_id(db: Session, incidencia_id: int):
    incidencia = (
        db.query(Incidencia)
        .filter(Incidencia.id == incidencia_id)
        .first()
    )

    if not incidencia:
        raise HTTPException(
            status_code=404,
            detail="Incidencia no encontrada"
        )

    return incidencia


def create_incidencia(db: Session, incidencia_data: IncidenciaCreate):
    existing = (
        db.query(Incidencia)
        .filter(Incidencia.name == incidencia_data.name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="La incidencia ya existe"
        )

    incidencia = Incidencia(
        name=incidencia_data.name,
        is_active=True
    )

    db.add(incidencia)
    db.commit()
    db.refresh(incidencia)

    return incidencia


def update_incidencia(
        db: Session,
        incidencia_id: int,
        incidencia_data: IncidenciaUpdate
):
    incidencia = get_incidencia_by_id(db, incidencia_id)

    data = incidencia_data.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(incidencia, field, value)

    db.commit()
    db.refresh(incidencia)

    return incidencia


def get_subincidencias(db: Session):
    return (
        db.query(Subincidencia)
        .order_by(Subincidencia.name.asc())
        .all()
    )


def get_subincidencia_by_id(db: Session, subincidencia_id: int):
    subincidencia = (
        db.query(Subincidencia)
        .filter(Subincidencia.id == subincidencia_id)
        .first()
    )

    if not subincidencia:
        raise HTTPException(
            status_code=404,
            detail="Subincidencia no encontrada"
        )

    return subincidencia


def get_subincidencias_by_incidencia(db: Session, incidencia_id: int):
    get_incidencia_by_id(db, incidencia_id)

    return (
        db.query(Subincidencia)
        .filter(Subincidencia.incidencia_id == incidencia_id)
        .filter(Subincidencia.is_active == True)
        .order_by(Subincidencia.name.asc())
        .all()
    )


def create_subincidencia(db: Session, subincidencia_data: SubincidenciaCreate):
    get_incidencia_by_id(db, subincidencia_data.incidencia_id)

    existing = (
        db.query(Subincidencia)
        .filter(Subincidencia.incidencia_id == subincidencia_data.incidencia_id)
        .filter(Subincidencia.name == subincidencia_data.name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="La subincidencia ya existe para esta incidencia"
        )

    subincidencia = Subincidencia(
        incidencia_id=subincidencia_data.incidencia_id,
        name=subincidencia_data.name,
        is_active=True
    )

    db.add(subincidencia)
    db.commit()
    db.refresh(subincidencia)

    return subincidencia


def update_subincidencia(
        db: Session,
        subincidencia_id: int,
        subincidencia_data: SubincidenciaUpdate
):
    subincidencia = get_subincidencia_by_id(db, subincidencia_id)

    data = subincidencia_data.model_dump(exclude_unset=True)

    if "incidencia_id" in data:
        get_incidencia_by_id(db, data["incidencia_id"])

    for field, value in data.items():
        setattr(subincidencia, field, value)

    db.commit()
    db.refresh(subincidencia)

    return subincidencia