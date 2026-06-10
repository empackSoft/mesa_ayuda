from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies.database import get_db

from schemas.incidencia import (
    IncidenciaCreate,
    IncidenciaUpdate,
    IncidenciaResponse
)

from schemas.subincidencia import (
    SubincidenciaCreate,
    SubincidenciaUpdate,
    SubincidenciaResponse
)

from services import incidenciaService


router = APIRouter(
    prefix="/incidencias",
    tags=["Incidencias"]
)


@router.get(
    "/",
    response_model=list[IncidenciaResponse]
)
def list_incidencias(db: Session = Depends(get_db)):
    return incidenciaService.get_incidencias(db)


@router.get(
    "/active",
    response_model=list[IncidenciaResponse]
)
def list_active_incidencias(db: Session = Depends(get_db)):
    return incidenciaService.get_active_incidencias(db)


@router.get(
    "/{incidencia_id}",
    response_model=IncidenciaResponse
)
def get_incidencia(
        incidencia_id: int,
        db: Session = Depends(get_db)
):
    return incidenciaService.get_incidencia_by_id(db, incidencia_id)


@router.post(
    "/",
    response_model=IncidenciaResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_incidencia(
        incidencia: IncidenciaCreate,
        db: Session = Depends(get_db)
):
    return incidenciaService.create_incidencia(db, incidencia)


@router.put(
    "/{incidencia_id}",
    response_model=IncidenciaResponse
)
def update_existing_incidencia(
        incidencia_id: int,
        incidencia: IncidenciaUpdate,
        db: Session = Depends(get_db)
):
    return incidenciaService.update_incidencia(
        db,
        incidencia_id,
        incidencia
    )


@router.get(
    "/{incidencia_id}/subincidencias",
    response_model=list[SubincidenciaResponse]
)
def list_subincidencias_by_incidencia(
        incidencia_id: int,
        db: Session = Depends(get_db)
):
    return incidenciaService.get_subincidencias_by_incidencia(
        db,
        incidencia_id
    )


@router.get(
    "/subincidencias/all",
    response_model=list[SubincidenciaResponse]
)
def list_subincidencias(db: Session = Depends(get_db)):
    return incidenciaService.get_subincidencias(db)


@router.post(
    "/subincidencias",
    response_model=SubincidenciaResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_subincidencia(
        subincidencia: SubincidenciaCreate,
        db: Session = Depends(get_db)
):
    return incidenciaService.create_subincidencia(db, subincidencia)


@router.put(
    "/subincidencias/{subincidencia_id}",
    response_model=SubincidenciaResponse
)
def update_existing_subincidencia(
        subincidencia_id: int,
        subincidencia: SubincidenciaUpdate,
        db: Session = Depends(get_db)
):
    return incidenciaService.update_subincidencia(
        db,
        subincidencia_id,
        subincidencia
    )