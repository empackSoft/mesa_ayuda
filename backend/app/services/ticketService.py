from sqlalchemy.orm import Session
from fastapi import UploadFile,HTTPException
from sqlalchemy.exc import IntegrityError

from models.user import User
from models.ticket import Ticket
from models.incidencia import Incidencia
from models.subincidencia import Subincidencia
from services.ticketHistoryService import create_history
import os
import shutil
import uuid
from models.ticketAttachment import TicketAttachment
from services.emailService import send_email, build_ticket_link

from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketStatusUpdate
)

# CONSTANTES
UPLOAD_FOLDER = "uploads/tickets"

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".zip"
}

MAX_FILE_SIZE = 10 * 1024 * 1024

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

VALID_TRANSITIONS = {
    "open": [
        "in_progress"
    ],

    "in_progress": [
        "pending",
        "resolved"
    ],

    "pending": [
        "in_progress",
        "resolved"
    ],

    "resolved": [
        "closed"
    ],

    "closed": []
}

def build_ticket_response(ticket: Ticket):
    return {
        "id": ticket.id,
        "incidencia_id": ticket.incidencia_id,
        "incidencia": ticket.incidencia.name if ticket.incidencia else None,
        "subincidencia_id": ticket.subincidencia_id,
        "subincidencia": ticket.subincidencia.name if ticket.subincidencia else None,
        "created_by_user_id": ticket.created_by_user_id,
        "created_by_user_name": ticket.created_by.name if ticket.created_by else None,
        "assigned_to_user_id": ticket.assigned_to_user_id,
        "assigned_to_user_name": ticket.assigned_to.name if ticket.assigned_to else None,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at
    }

def assign_ticket(
        db: Session,
        ticket_id: int,
        assigned_to_user_id: int
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    assigned_user = (
        db.query(User)
        .filter(User.id == assigned_to_user_id)
        .first()
    )

    if assigned_user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario asignado no encontrado"
        )

    if assigned_user.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="No se puede asignar a un usuario inactivo"
        )

    if assigned_user.role not in ["support", "admin"]:
        raise HTTPException(
            status_code=400,
            detail="El ticket solo puede asignarse a soporte o administrador"
        )

    old_user = ticket.assigned_to_user_id

    ticket.assigned_to_user_id = assigned_user.id
    ticket.status = "in_progress"

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=assigned_user.id,
        action="ASSIGN",
        old_value=str(old_user) if old_user else None,
        new_value=str(assigned_user.id)
    )
    # Notificar al técnico asignado
    if assigned_user.email:
        link = build_ticket_link(ticket.id)
        send_email(
            to=assigned_user.email,
            subject=f"Se te ha asignado el ticket #{ticket.id}",
            body=(
                f"Hola {assigned_user.name},\n\n"
                f"Se te ha asignado el ticket #{ticket.id}.\n\n"
                f"Puedes verlo aquí: {link}\n\n"
                f"Sistema Mesa de Ayuda EmPack"
            )
        )

    return build_ticket_response(ticket)

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
        ticket_data: TicketCreate,
        current_user=None
):
    validate_catalog_relation(
        db=db,
        incidencia_id=ticket_data.incidencia_id,
        subincidencia_id=ticket_data.subincidencia_id
    )

    new_ticket = Ticket(
        incidencia_id=ticket_data.incidencia_id,
        subincidencia_id=ticket_data.subincidencia_id,
        created_by_user_id=current_user.id if current_user else None,
        description=ticket_data.description,
        status="open",
        priority="medium"
    )

    try:
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        create_history(
            db=db,
            ticket_id=new_ticket.id,
            user_id=new_ticket.created_by_user_id,
            action="CREATE",
            old_value=None,
            new_value="Ticket creado"
        )
        # Notificar al equipo de soporte que hay un ticket nuevo
        support_users = (
            db.query(User)
            .filter(
                User.role.in_(["support", "admin"]),
                User.is_active == True
            )
            .all()
        )

        link = build_ticket_link(new_ticket.id)

        for support_user in support_users:
            if support_user.email:
                send_email(
                    to=support_user.email,
                    subject=f"Nuevo ticket #{new_ticket.id} creado",
                    body=(
                        f"Hola {support_user.name},\n\n"
                        f"Se ha creado un nuevo ticket #{new_ticket.id}.\n\n"
                        f"Descripción: {new_ticket.description}\n\n"
                        f"Puedes verlo aquí: {link}\n\n"
                        f"Sistema Mesa de Ayuda EmPack"
                    )
                )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el ticket por una relación inválida"
        )

    return build_ticket_response(new_ticket)

def get_tickets(
        db: Session,
        status: str = None,
        priority: str = None,
        incidencia_id: int = None,
        subincidencia_id: int = None,
        created_from=None,
        created_to=None,
        current_user=None
):
    query = db.query(Ticket)

    if current_user and current_user.role == "user":
        query = query.filter(Ticket.created_by_user_id == current_user.id)

    if status:
        if status not in VALID_STATUS:
            raise HTTPException(
                status_code=400,
                detail="Estado inválido"
            )

        query = query.filter(Ticket.status == status)

    if priority:
        if priority not in VALID_PRIORITY:
            raise HTTPException(
                status_code=400,
                detail="Prioridad inválida"
            )

        query = query.filter(Ticket.priority == priority)

    if incidencia_id:
        query = query.filter(Ticket.incidencia_id == incidencia_id)

    if subincidencia_id:
        query = query.filter(Ticket.subincidencia_id == subincidencia_id)

    if created_from:
        query = query.filter(Ticket.created_at >= created_from)

    if created_to:
        query = query.filter(Ticket.created_at <= created_to)

    tickets = (
        query
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
    changes = []

    for field, value in data.items():
        old_value = getattr(ticket, field)

        if old_value != value:

            changes.append(
                (
                    field,
                    str(old_value),
                    str(value)
                )
            )

        setattr(ticket, field, value)

    try:
        db.commit()
        db.refresh(ticket)

        for field, old_value, new_value in changes:
            create_history(
                db=db,
                ticket_id=ticket.id,
                user_id=ticket.assigned_to_user_id,
                action=f"UPDATE_{field.upper()}",
                old_value=old_value,
                new_value=new_value
            )

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
    old_status = ticket.status

    ticket.status = "closed"

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=ticket.assigned_to_user_id,
        action="CLOSE",
        old_value=old_status,
        new_value="closed"
    )

    # Notificar al creador del ticket sobre el cierre
    creator = (
        db.query(User)
        .filter(User.id == ticket.created_by_user_id)
        .first()
    )

    if creator and creator.email:
        link = build_ticket_link(ticket.id)
        send_email(
            to=creator.email,
            subject=f"Tu ticket #{ticket.id} ha sido cerrado",
            body=(
                f"Hola {creator.name},\n\n"
                f"Tu ticket #{ticket.id} ha sido cerrado.\n\n"
                f"Puedes verlo aquí: {link}\n\n"
                f"Sistema Mesa de Ayuda EmPack"
            )
        )

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


def change_ticket_status(
        db: Session,
        ticket_id: int,
        status_data: TicketStatusUpdate
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    new_status = status_data.status

    if new_status not in VALID_STATUS:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido"
        )

    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="El ticket ya está cerrado"
        )

    if ticket.assigned_to_user_id is None:
        raise HTTPException(
            status_code=400,
            detail="El ticket debe estar asignado antes de cambiar de estado"
        )

    valid_next = VALID_TRANSITIONS[ticket.status]

    if new_status not in valid_next:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cambiar de {ticket.status} a {new_status}"
        )

    old_status = ticket.status
    ticket.status = new_status

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=ticket.assigned_to_user_id,
        action="STATUS",
        old_value=old_status,
        new_value=new_status
    )
    # Notificar al creador del ticket sobre el cambio de estado
    creator = (
        db.query(User)
        .filter(User.id == ticket.created_by_user_id)
        .first()
    )

    if creator and creator.email:
        link = build_ticket_link(ticket.id)
        send_email(
            to=creator.email,
            subject=f"Tu ticket #{ticket.id} cambió de estado",
            body=(
                f"Hola {creator.name},\n\n"
                f"El estado de tu ticket #{ticket.id} cambió a: {new_status}.\n\n"
                f"Puedes verlo aquí: {link}\n\n"
                f"Sistema Mesa de Ayuda EmPack"
            )
        )


    return build_ticket_response(ticket)

def upload_attachment(
        db: Session,
        ticket_id: int,
        file: UploadFile,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="No se puede adjuntar archivos a un ticket cerrado"
        )

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido"
        )

    contents = file.file.read()

    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío"
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="El archivo excede el tamaño máximo permitido (10 MB)"
        )

    unique_name = f"{uuid.uuid4()}{extension}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    new_attachment = TicketAttachment(
        ticket_id=ticket.id,
        file_path=file_path,
        original_name=file.filename,
        uploaded_by=current_user.id if current_user else None
    )

    db.add(new_attachment)
    db.commit()
    db.refresh(new_attachment)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id if current_user else None,
        action="UPLOAD_ATTACHMENT",
        old_value=None,
        new_value=file_path
    )

    return new_attachment



def list_attachments(
        db: Session,
        ticket_id: int
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    return (
        db.query(TicketAttachment)
        .filter(TicketAttachment.ticket_id == ticket.id)
        .order_by(TicketAttachment.id.desc())
        .all()
    )


def get_attachment(
        db: Session,
        ticket_id: int,
        attachment_id: int
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    attachment = (
        db.query(TicketAttachment)
        .filter(
            TicketAttachment.id == attachment_id,
            TicketAttachment.ticket_id == ticket.id
        )
        .first()
    )

    if attachment is None:
        raise HTTPException(
            status_code=404,
            detail="Adjunto no encontrado"
        )

    if not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=404,
            detail="El archivo adjunto no se encuentra en el servidor"
        )

    return attachment