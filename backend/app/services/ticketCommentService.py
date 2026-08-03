from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.ticket import Ticket
from models.ticketComment import TicketComment
from services.ticketHistoryService import create_history
from schemas.ticketComment import TicketCommentCreate
from services.emailService import send_email, build_ticket_link
from models.user import User

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


def create_comment(
        db: Session,
        ticket_id: int,
        comment_data: TicketCommentCreate,
        current_user
):
    ticket = find_ticket_or_404(db, ticket_id)

    # Bloquear comentarios en tickets cerrados
    if ticket.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="No se puede comentar en un ticket cerrado"
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

    # Notificaciones por correo
    link = build_ticket_link(ticket.id)

    if not is_internal:
        # COMENTARIO PÚBLICO
        if current_user.role in ["support", "admin"]:
            # Comenta soporte -> avisar al creador del ticket
            creator = (
                db.query(User)
                .filter(User.id == ticket.created_by_user_id)
                .first()
            )

            if creator and creator.email:
                send_email(
                    to=creator.email,
                    subject=f"Nuevo comentario en tu ticket #{ticket.id}",
                    body=(
                        f"Hola {creator.name},\n\n"
                        f"Hay un nuevo comentario en tu ticket #{ticket.id}.\n\n"
                        f"Puedes verlo y responder aquí: {link}\n\n"
                        f"Sistema Mesa de Ayuda EmPack"
                    )
                )
        else:
            # Comenta el usuario -> avisar al técnico asignado
            if ticket.assigned_to_user_id:
                technician = (
                    db.query(User)
                    .filter(User.id == ticket.assigned_to_user_id)
                    .first()
                )

                if technician and technician.email:
                    send_email(
                        to=technician.email,
                        subject=f"Nuevo comentario en el ticket #{ticket.id}",
                        body=(
                            f"Hola {technician.name},\n\n"
                            f"El usuario agregó un comentario en el ticket #{ticket.id}.\n\n"
                            f"Puedes verlo y responder aquí: {link}\n\n"
                            f"Sistema Mesa de Ayuda EmPack"
                        )
                    )
    else:
        # COMENTARIO INTERNO -> avisar SOLO a soporte/admin, NUNCA al usuario
        staff_users = (
            db.query(User)
            .filter(
                User.role.in_(["support", "admin"]),
                User.is_active == True,
                User.id != current_user.id  # no notificar al que escribió
            )
            .all()
        )

        for staff in staff_users:
            if staff.email:
                send_email(
                    to=staff.email,
                    subject=f"Nuevo comentario interno en el ticket #{ticket.id}",
                    body=(
                        f"Hola {staff.name},\n\n"
                        f"Se agregó un comentario interno en el ticket #{ticket.id}.\n\n"
                        f"Puedes verlo aquí: {link}\n\n"
                        f"Sistema Mesa de Ayuda EmPack"
                    )
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