from datetime import datetime, timedelta

from sqlalchemy import or_, case, func
from sqlalchemy.orm import Session, aliased, joinedload
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
from services.ticketNotifyService import notify_ticket, STATUS_LABELS, CLOSING_POLICY

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
    "pending",
    "resolved",
    "closed",
    "cancelled"
]

# Estados finales: ya no admiten cambios, comentarios ni archivos
FINAL_STATUSES = [
    "closed",
    "cancelled"
]

# Se puede cancelar mientras Soporte no lo haya resuelto
CANCELLABLE_STATUSES = [
    "open",
    "in_progress",
    "pending"
]

# Tiempo que tiene el usuario para confirmar la solución y contestar la encuesta
FEEDBACK_HOURS = 24

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
        "in_progress",
        "closed"
    ],

    "closed": [],

    "cancelled": []
}

PRIORITY_ORDER = case(
    {"low": 0, "medium": 1, "high": 2, "urgent": 3},
    value=Ticket.priority,
    else_=1
)

MAX_PAGE_SIZE = 100


def feedback_state(ticket: Ticket):
    """
    Qué le falta responder al solicitante:
    - "confirm": está resuelto; debe confirmar (y calificar) o reabrirlo.
    - "survey": ya está cerrado; solo falta la encuesta.
    Los tickets sin resolved_at/closed_at (importados o anteriores a la encuesta) no piden nada.
    """
    if ticket.survey is not None:
        return None
    if ticket.status == "resolved" and ticket.resolved_at is not None:
        return "confirm"
    if ticket.status == "closed" and ticket.closed_at is not None:
        return "survey"
    return None


def feedback_due_at(ticket: Ticket):
    state = feedback_state(ticket)
    if state == "confirm":
        return ticket.resolved_at + timedelta(hours=FEEDBACK_HOURS)
    if state == "survey":
        return ticket.closed_at + timedelta(hours=FEEDBACK_HOURS)
    return None


def ensure_not_final(ticket: Ticket):
    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="El ticket ya está cerrado"
        )

    if ticket.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="El ticket está cancelado"
        )

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
        "location_id": ticket.location_id,
        "location_name": ticket.location.name if ticket.location else None,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "resolved_at": ticket.resolved_at,
        "closed_at": ticket.closed_at,
        "cancel_reason": ticket.cancel_reason,
        "feedback_state": feedback_state(ticket),
        "feedback_due_at": feedback_due_at(ticket),
        "survey": {
            "rating": ticket.survey.rating,
            "comment": ticket.survey.comment,
            "is_auto": ticket.survey.is_auto,
            "created_at": ticket.survey.created_at
        } if ticket.survey else None
    }

def assign_ticket(
        db: Session,
        ticket_id: int,
        assigned_to_user_id: int,
        current_user=None
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

    ensure_not_final(ticket)

    old_user = ticket.assigned_to_user_id

    ticket.assigned_to_user_id = assigned_user.id
    ticket.status = "in_progress"
    ticket.resolved_at = None

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id if current_user else None,
        action="ASSIGN",
        old_value=str(old_user) if old_user else None,
        new_value=str(assigned_user.id)
    )
    notify_ticket(
        db, ticket,
        subject=f"Asignado a {assigned_user.name}",
        message=f"El ticket #{ticket.id} se asignó a {assigned_user.name}.",
        actor=current_user
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


def ensure_ticket_access(ticket: Ticket, current_user=None):
    # Un "user" solo puede ver y adjuntar en los tickets que él creó
    if (
        current_user is not None
        and current_user.role == "user"
        and ticket.created_by_user_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="No tienes acceso a este ticket"
        )

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

    # El ticket se relaciona en automático con la ubicación de quien lo levanta
    if current_user is not None and current_user.role == "user" and current_user.location_id is None:
        raise HTTPException(
            status_code=400,
            detail="Tu cuenta no tiene ubicación asignada. Pide a un administrador que te la asigne."
        )

    new_ticket = Ticket(
        incidencia_id=ticket_data.incidencia_id,
        subincidencia_id=ticket_data.subincidencia_id,
        created_by_user_id=current_user.id if current_user else None,
        location_id=current_user.location_id if current_user else None,
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
        # Aviso al que lo levantó y a todo el equipo de soporte (aún no hay asignado)
        notify_ticket(
            db, new_ticket,
            subject=f"Nuevo ticket: {new_ticket.incidencia.name}",
            message=f"Se levantó el ticket #{new_ticket.id}.",
            actor=current_user,
            footer=CLOSING_POLICY,
            kind="new_ticket"
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo crear el ticket por una relación inválida"
        )

    return build_ticket_response(new_ticket)

def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_tickets(
        db: Session,
        status: str = None,
        priority: str = None,
        incidencia_id: int = None,
        subincidencia_id: int = None,
        created_from=None,
        created_to=None,
        q: str = None,
        assigned_to_me: bool = False,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "id",
        sort_desc: bool = True,
        current_user=None
):
    """
    Lista paginada. `status` acepta un estado, "active" (sin cerrar ni cancelar) o "all".
    Devuelve también cuántos hay por estado con los demás filtros, para las pestañas del front.
    """
    creator = aliased(User)
    assignee = aliased(User)

    query = (
        db.query(Ticket)
        .join(Incidencia, Incidencia.id == Ticket.incidencia_id)
        .join(Subincidencia, Subincidencia.id == Ticket.subincidencia_id)
        .outerjoin(creator, creator.id == Ticket.created_by_user_id)
        .outerjoin(assignee, assignee.id == Ticket.assigned_to_user_id)
    )

    if current_user and current_user.role == "user":
        query = query.filter(Ticket.created_by_user_id == current_user.id)

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

    if assigned_to_me and current_user:
        query = query.filter(Ticket.assigned_to_user_id == current_user.id)

    q = (q or "").strip()
    if q:
        pattern = f"%{_escape_like(q)}%"
        conditions = [
            Ticket.description.ilike(pattern, escape="\\"),
            Incidencia.name.ilike(pattern, escape="\\"),
            Subincidencia.name.ilike(pattern, escape="\\"),
            creator.name.ilike(pattern, escape="\\"),
            assignee.name.ilike(pattern, escape="\\"),
        ]
        number = q.lstrip("#")
        if number.isdigit() and len(number) < 10:
            conditions.append(Ticket.id == int(number))
        query = query.filter(or_(*conditions))

    # Conteo por estado con todos los filtros menos el de estado
    status_counts = dict(
        query
        .with_entities(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )

    if status == "active":
        query = query.filter(Ticket.status.notin_(FINAL_STATUSES))
    elif status and status != "all":
        if status not in VALID_STATUS:
            raise HTTPException(
                status_code=400,
                detail="Estado inválido"
            )

        query = query.filter(Ticket.status == status)

    total = query.count()

    sort_columns = {
        "id": Ticket.id,
        "created_at": Ticket.created_at,
        "status": Ticket.status,
        "priority": PRIORITY_ORDER,
        "created_by_user_name": creator.name,
        "assigned_to_user_name": assignee.name,
    }
    column = sort_columns.get(sort_by, Ticket.id)
    order = column.desc().nullslast() if sort_desc else column.asc().nullslast()

    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    page = max(1, page)

    tickets = (
        query
        .options(
            joinedload(Ticket.incidencia),
            joinedload(Ticket.subincidencia),
            joinedload(Ticket.created_by),
            joinedload(Ticket.assigned_to),
            joinedload(Ticket.location),
            joinedload(Ticket.survey)
        )
        .order_by(order, Ticket.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            build_ticket_response(ticket)
            for ticket in tickets
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "status_counts": status_counts
    }

def get_ticket_by_id(
        db: Session,
        ticket_id: int,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    ensure_ticket_access(ticket, current_user)

    return build_ticket_response(ticket)


def update_ticket(
        db: Session,
        ticket_id: int,
        ticket_data: TicketUpdate,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    ensure_not_final(ticket)

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
                user_id=current_user.id if current_user else None,
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
        ticket_id: int,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    ensure_not_final(ticket)

    old_status = ticket.status

    ticket.status = "closed"
    ticket.closed_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id if current_user else None,
        action="CLOSE",
        old_value=old_status,
        new_value="closed"
    )

    notify_ticket(
        db, ticket,
        subject="Cerrado",
        message=(
            f"El ticket #{ticket.id} fue cerrado.\n\n"
            f"Entra al sistema para calificar la atención (encuesta obligatoria). "
            f"Si no respondes en {FEEDBACK_HOURS} horas, se registrará con 5 estrellas."
        ),
        actor=current_user
    )

    return build_ticket_response(ticket)


# Los tickets no se borran (auditoría): se cancelan con un motivo
def cancel_ticket(
        db: Session,
        ticket_id: int,
        reason: str,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    ensure_ticket_access(ticket, current_user)
    ensure_not_final(ticket)

    if ticket.status not in CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Un ticket resuelto ya no se puede cancelar"
        )

    old_status = ticket.status

    ticket.status = "cancelled"
    ticket.cancel_reason = reason
    ticket.resolved_at = None

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id if current_user else None,
        action="CANCEL",
        old_value=old_status,
        new_value=reason
    )

    who = current_user.name if current_user else "Sistema"
    notify_ticket(
        db, ticket,
        subject="Cancelado",
        message=f"{who} canceló el ticket #{ticket.id}.\n\nMotivo: {reason}",
        actor=current_user
    )

    return build_ticket_response(ticket)


def change_ticket_status(
        db: Session,
        ticket_id: int,
        status_data: TicketStatusUpdate,
        current_user=None
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

    ensure_not_final(ticket)

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

    # Cerrar tiene su propio flujo (fecha de cierre, encuesta)
    if new_status == "closed":
        return close_ticket(db, ticket_id, current_user)

    old_status = ticket.status
    ticket.status = new_status
    # Al resolverse empiezan a correr las 24 h para que el usuario confirme
    ticket.resolved_at = datetime.utcnow() if new_status == "resolved" else None

    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id if current_user else None,
        action="STATUS",
        old_value=old_status,
        new_value=new_status
    )
    new_label = STATUS_LABELS.get(new_status, new_status)
    message = f"El estado del ticket #{ticket.id} cambió a: {new_label}."
    if new_status == "resolved":
        message += (
            f"\n\nEntra al sistema para confirmar si quedó solucionado y calificar la atención. "
            f"Si no respondes en {FEEDBACK_HOURS} horas, el ticket se cerrará automáticamente "
            f"y la encuesta se registrará con 5 estrellas."
        )
    notify_ticket(
        db, ticket,
        subject=f"Estado: {new_label}",
        message=message,
        actor=current_user
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

    ensure_ticket_access(ticket, current_user)

    if ticket.status in FINAL_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="No se pueden adjuntar archivos a un ticket cerrado o cancelado"
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
        ticket_id: int,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    ensure_ticket_access(ticket, current_user)

    return (
        db.query(TicketAttachment)
        .filter(TicketAttachment.ticket_id == ticket.id)
        .order_by(TicketAttachment.id.desc())
        .all()
    )


def get_attachment(
        db: Session,
        ticket_id: int,
        attachment_id: int,
        current_user=None
):
    ticket = find_ticket_by_id(
        db,
        ticket_id
    )

    ensure_ticket_access(ticket, current_user)

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