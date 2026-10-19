from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from models.ticket import Ticket
from models.ticketComment import TicketComment
from models.ticketSurvey import TicketSurvey
from services.ticketHistoryService import create_history
from services.ticketNotifyService import notify_ticket
from services.ticketService import (
    FEEDBACK_HOURS,
    build_ticket_response,
    feedback_state,
    find_ticket_by_id
)

# Cierre del ciclo de un ticket por parte de quien lo levantó:
# - Resuelto → el usuario confirma (y califica, obligatorio) → Cerrado.
# - Resuelto → el usuario dice que sigue el problema → En progreso.
# - Sin respuesta en 24 h → se cierra solo y la encuesta queda en 5 estrellas sin comentario.

AUTO_RATING = 5


def ensure_creator(ticket: Ticket, current_user):
    if ticket.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Solo quien levantó el ticket puede responder"
        )


def _save_survey(db: Session, ticket: Ticket, rating: int, comment, user_id, is_auto: bool):
    db.add(TicketSurvey(
        ticket_id=ticket.id,
        user_id=user_id,
        rating=rating,
        comment=comment,
        is_auto=is_auto
    ))


def stars(rating: int) -> str:
    return "★" * rating + "☆" * (5 - rating)


def submit_survey(
        db: Session,
        ticket_id: int,
        rating: int,
        comment,
        current_user
):
    ticket = find_ticket_by_id(db, ticket_id)
    ensure_creator(ticket, current_user)

    state = feedback_state(ticket)
    if state is None:
        raise HTTPException(
            status_code=400,
            detail="Este ticket no tiene una encuesta pendiente"
        )

    comment = (comment or "").strip() or None
    now = datetime.utcnow()

    if state == "confirm":
        ticket.status = "closed"
        ticket.closed_at = now

    _save_survey(db, ticket, rating, comment, current_user.id, is_auto=False)
    db.commit()
    db.refresh(ticket)

    if state == "confirm":
        create_history(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="CONFIRM",
            old_value="resolved",
            new_value="closed"
        )

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="SURVEY",
        old_value=None,
        new_value=str(rating)
    )

    message = (
        f"{current_user.name} confirmó que el ticket #{ticket.id} quedó solucionado y lo cerró."
        if state == "confirm"
        else f"{current_user.name} calificó la atención del ticket #{ticket.id}."
    )
    message += f"\n\nCalificación: {stars(rating)} ({rating} de 5)"
    if comment:
        message += f"\nComentario: {comment}"

    notify_ticket(
        db, ticket,
        subject="Cerrado por el usuario" if state == "confirm" else f"Calificación: {rating} de 5",
        message=message,
        include_creator=False,
        actor=current_user
    )

    return build_ticket_response(ticket)


def reopen_ticket(
        db: Session,
        ticket_id: int,
        reason: str,
        current_user
):
    ticket = find_ticket_by_id(db, ticket_id)
    ensure_creator(ticket, current_user)

    if feedback_state(ticket) != "confirm":
        raise HTTPException(
            status_code=400,
            detail="Solo se puede reabrir un ticket resuelto que esté esperando tu confirmación"
        )

    ticket.status = "in_progress"
    ticket.resolved_at = None

    # El motivo queda en la conversación para que Soporte lo vea con el resto del hilo
    db.add(TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        body=f"El problema continúa: {reason}",
        is_internal=False
    ))
    db.commit()
    db.refresh(ticket)

    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="REOPEN",
        old_value="resolved",
        new_value="in_progress"
    )

    notify_ticket(
        db, ticket,
        subject="Reabierto: el problema continúa",
        message=f"{current_user.name} indicó que el problema del ticket #{ticket.id} continúa.\n\nMotivo: {reason}",
        include_creator=False,
        actor=current_user
    )

    return build_ticket_response(ticket)


def get_pending_feedback(db: Session, current_user):
    """Tickets del usuario que esperan su confirmación o su encuesta (el front los pide al entrar)."""
    tickets = (
        db.query(Ticket)
        .options(joinedload(Ticket.survey), joinedload(Ticket.incidencia), joinedload(Ticket.subincidencia))
        .filter(
            Ticket.created_by_user_id == current_user.id,
            Ticket.status.in_(["resolved", "closed"]),
            ~Ticket.survey.has()
        )
        .filter(
            ((Ticket.status == "resolved") & Ticket.resolved_at.isnot(None))
            | ((Ticket.status == "closed") & Ticket.closed_at.isnot(None))
        )
        .order_by(Ticket.id.asc())
        .all()
    )

    return [build_ticket_response(ticket) for ticket in tickets]


def auto_close_expired(db: Session):
    """
    Lo corre el proceso programado (scheduledJobs). Pasadas 24 h sin respuesta:
    - Resueltos → se cierran y la encuesta queda en 5 estrellas.
    - Cerrados sin encuesta → la encuesta queda en 5 estrellas.
    """
    limit = datetime.utcnow() - timedelta(hours=FEEDBACK_HOURS)

    expired_resolved = (
        db.query(Ticket)
        .filter(
            Ticket.status == "resolved",
            Ticket.resolved_at.isnot(None),
            Ticket.resolved_at <= limit,
            ~Ticket.survey.has()
        )
        .all()
    )

    for ticket in expired_resolved:
        ticket.status = "closed"
        ticket.closed_at = datetime.utcnow()
        _save_survey(db, ticket, AUTO_RATING, None, None, is_auto=True)
        db.commit()
        db.refresh(ticket)

        create_history(
            db=db,
            ticket_id=ticket.id,
            user_id=None,
            action="AUTO_CLOSE",
            old_value="resolved",
            new_value="closed"
        )
        create_history(
            db=db,
            ticket_id=ticket.id,
            user_id=None,
            action="SURVEY",
            old_value="auto",
            new_value=str(AUTO_RATING)
        )

        notify_ticket(
            db, ticket,
            subject="Cerrado automáticamente",
            message=(
                f"El ticket #{ticket.id} se cerró automáticamente: pasaron {FEEDBACK_HOURS} horas "
                f"desde que se marcó como resuelto sin que hubiera respuesta.\n\n"
                f"La encuesta se registró con {AUTO_RATING} estrellas, sin comentarios."
            )
        )

    expired_surveys = (
        db.query(Ticket)
        .filter(
            Ticket.status == "closed",
            Ticket.closed_at.isnot(None),
            Ticket.closed_at <= limit,
            ~Ticket.survey.has()
        )
        .all()
    )

    for ticket in expired_surveys:
        _save_survey(db, ticket, AUTO_RATING, None, None, is_auto=True)
        db.commit()

        create_history(
            db=db,
            ticket_id=ticket.id,
            user_id=None,
            action="SURVEY",
            old_value="auto",
            new_value=str(AUTO_RATING)
        )

    return len(expired_resolved), len(expired_surveys)
