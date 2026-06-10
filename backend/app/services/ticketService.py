from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from models.ticket import Ticket
from models.incidencia import Incidencia
from models.subincidencia import Subincidencia

from schemas.ticket import TicketCreate, TicketUpdate


VALID_STATUS = [
    "open",
    "in_progress",
    "resolved",
    "closed"
]

VALID_PRIORITY = [
    "low",
    "medium",
    "high",
    "urgent"
]


def build_ticket_response(ticket: Ticket):
    return {
        "id": ticket.id,
        "incidencia_id": ticket.incidencia_id,
        "incidencia": ticket.incidencia.name if ticket.incidencia else None,
        "subincidencia_id": ticket.subincidencia_id,
        "subincidencia": ticket.subincidencia.name if ticket.subincidencia else None,
        "description": ticket.description,
        "attachment_path": ticket.attachment_path,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at
    }


def validate_catalog_relation(
        db: Session,
        incidencia_id: int,
        subincidencia_id: int
):
    incidencia = (
        db.query(Incidencia)
        .filter(Incidencia.id == incidencia_id)
        .first()
    )

    if incidencia is None:
        raise HTTPException(
            status_code=404,
            detail="Incidencia no encontrada"
        )

    subincidencia = (
        db.query(Subincidencia)
        .filter(Subincidencia.id == subincidencia_id)
        .first()
    )

    if subincidencia is None:
        raise HTTPException(
            status_code=404,
            detail="Subincidencia no encontrada"
        )

    if int(subincidencia.incidencia_id) != int(incidencia_id):
        raise HTTPException(
            status_code=400,
            detail="La subincidencia no pertenece a la incidencia indicada"
        )

    if incidencia.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="La incidencia está inactiva"
        )

    if subincidencia.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="La subincidencia está inactiva"
        )


def find_ticket_by_id(
        db: Session,
        ticket_id: int
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket no encontrado"
        )

    return ticket


def create_ticket(
        db: Session,
        ticket_data: TicketCreate
):
    validate_catalog_relation(
        db=db,
        incidencia_id=ticket_data.incidencia_id,
        subincidencia_id=ticket_data.subincidencia_id
    )

    new_ticket = Ticket(
        incidencia_id=ticket_data.incidencia_id,
        subincidencia_id=ticket_data.subincidencia_id,
        description=ticket_data.description,
        attachment_path=ticket_data.attachment_path,
        status="open",
        priority="medium"
    )

    try:
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el ticket por una relación inválida"
        )

    return build_ticket_response(new_ticket)


def get_tickets(db: Session):
    tickets = (
        db.query(Ticket)
        .order_by(Ticket.id.desc())
        .all()
    )

    return [
        build_ticket_response(ticket)
        for ticket in tickets
    ]


def get_ticket_by_id(
        db: Session,
        ticket_id: int
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    return build_ticket_response(ticket)


def update_ticket(
        db: Session,
        ticket_id: int,
        ticket_data: TicketUpdate
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    data = ticket_data.model_dump(exclude_unset=True)

    new_incidencia_id = data.get(
        "incidencia_id",
        ticket.incidencia_id
    )

    new_subincidencia_id = data.get(
        "subincidencia_id",
        ticket.subincidencia_id
    )

    if "incidencia_id" in data or "subincidencia_id" in data:
        validate_catalog_relation(
            db=db,
            incidencia_id=new_incidencia_id,
            subincidencia_id=new_subincidencia_id
        )

    if "status" in data and data["status"] not in VALID_STATUS:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido"
        )

    if "priority" in data and data["priority"] not in VALID_PRIORITY:
        raise HTTPException(
            status_code=400,
            detail="Prioridad inválida"
        )

    for field, value in data.items():
        setattr(ticket, field, value)

    try:
        db.commit()
        db.refresh(ticket)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar el ticket por una relación inválida"
        )

    return build_ticket_response(ticket)


def close_ticket(
        db: Session,
        ticket_id: int
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="El ticket ya está cerrado"
        )

    ticket.status = "closed"

    db.commit()
    db.refresh(ticket)

    return build_ticket_response(ticket)


def delete_ticket(
        db: Session,
        ticket_id: int
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    db.delete(ticket)
    db.commit()

    return {
        "message": "Ticket eliminado correctamente",
        "ticket_id": ticket_id
    }