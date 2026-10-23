from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.ticket import Ticket
from models.ticketComment import TicketComment
from services.ticketHistoryService import create_history
from schemas.ticketComment import TicketCommentCreate
from services.ticketNotifyService import notify_ticket

def find_ticket_or_404(db: Session, ticket_id: int):
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


ROLE_LABELS = {
    "user": "Usuario",
    "support": "Soporte",
    "admin": "Administrador",
}


def _excerpt_message(author, role, created_at, body, is_internal=False, is_new=False) -> dict:
    return {
        "author": author or "Usuario eliminado",
        "role": role,
        "created_at": created_at,
        "body": body,
        "is_internal": is_internal,
        "is_new": is_new,
    }


def build_conversation_excerpt(db: Session, ticket: Ticket, new_comment: TicketComment) -> dict:
    """
    Fragmento de la conversación para el correo de un comentario: el último mensaje
    de la otra parte (al que se está respondiendo) y el nuevo. La descripción del ticket
    cuenta como el primer mensaje del solicitante. Si el comentario es público,
    las notas internas no entran (el correo le llega al usuario).
    """
    query = db.query(TicketComment).filter(
        TicketComment.ticket_id == ticket.id,
        TicketComment.id != new_comment.id
    )
    if not new_comment.is_internal:
        query = query.filter(TicketComment.is_internal.is_(False))

    comments = query.order_by(TicketComment.id.asc()).all()

    creator = ticket.created_by
    thread = [_excerpt_message(
        creator.name if creator else None, "Solicitante", ticket.created_at, ticket.description
    )] + [
        _excerpt_message(
            c.user_name, ROLE_LABELS.get(c.user_role), c.created_at, c.body, is_internal=c.is_internal
        )
        for c in comments
    ]
    thread_authors = [ticket.created_by_user_id] + [c.user_id for c in comments]

    # Último mensaje de alguien distinto al autor; si no hay, el último del hilo
    previous_index = next(
        (i for i in range(len(thread) - 1, -1, -1) if thread_authors[i] != new_comment.user_id),
        len(thread) - 1
    )

    return {
        "older": previous_index > 0 or previous_index < len(thread) - 1,
        "messages": [
            thread[previous_index],
            _excerpt_message(
                new_comment.user_name, ROLE_LABELS.get(new_comment.user_role), new_comment.created_at,
                new_comment.body, is_internal=new_comment.is_internal, is_new=True
            ),
        ],
    }


def create_comment(
        db: Session,
        ticket_id: int,
        comment_data: TicketCommentCreate,
        current_user
):
    ticket = find_ticket_or_404(db, ticket_id)

    # Bloquear comentarios en tickets cerrados o cancelados
    if ticket.status in ["closed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail="No se puede comentar en un ticket cerrado o cancelado"
        )

    is_internal = comment_data.is_internal

    # Reglas por rol
    if current_user.role == "user":
        # El usuario solo comenta en SUS tickets
        if ticket.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No puedes comentar en un ticket que no es tuyo"
            )

        # El usuario solo puede escribir comentarios públicos
        if is_internal:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para escribir comentarios internos"
            )

    new_comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        body=comment_data.body,
        is_internal=is_internal
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="COMMENT",
        old_value=None,
        new_value="Comentario interno" if is_internal else "Comentario público"
    )

    # Notificación por correo: las notas internas NUNCA llegan al usuario
    kind = "Nota interna" if is_internal else "Nuevo comentario"
    notify_ticket(
        db, ticket,
        subject=f"{kind} de {current_user.name}",
        message=(
            f"{current_user.name} agregó una nota interna al ticket #{ticket.id}."
            if is_internal
            else f"{current_user.name} escribió en el ticket #{ticket.id}."
        ),
        include_creator=not is_internal,
        actor=current_user,
        conversation=build_conversation_excerpt(db, ticket, new_comment)
    )

    return new_comment


def list_comments(
        db: Session,
        ticket_id: int,
        current_user
):
    ticket = find_ticket_or_404(db, ticket_id)

    query = (
        db.query(TicketComment)
        .filter(TicketComment.ticket_id == ticket.id)
    )

    if current_user.role == "user":
        # Solo sus propios tickets
        if ticket.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="No puedes ver los comentarios de este ticket"
            )

        # Solo comentarios públicos
        query = query.filter(TicketComment.is_internal == False)

    return (
        query
        .order_by(TicketComment.id.asc())
        .all()
    )