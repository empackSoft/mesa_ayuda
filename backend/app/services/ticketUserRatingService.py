from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.ticketUserRating import TicketUserRating
from models.user import User
from services.ticketHistoryService import create_history
from services.ticketService import ensure_ticket_access, find_ticket_by_id

# Soporte califica al usuario que levantó el ticket, una vez que ya está resuelto, cerrado o
# cancelado. Sirve para detectar usuarios que no responden, responden mal o dan datos falsos.
# Lo puede hacer el técnico asignado o un admin. El usuario que levantó el ticket también la ve
# (solo lectura) para que tenga retroalimentación de cómo atendió el ticket.

RATEABLE_STATUSES = ["resolved", "closed", "cancelled"]

USER_RATING_REASONS = [
    "no_response",   # no respondió
    "bad_response",  # respondió mal
    "false_info",    # dio información falsa
]


def _ensure_can_rate(ticket, current_user):
    if current_user.role != "admin" and ticket.assigned_to_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Solo el técnico asignado o un administrador puede calificar al usuario"
        )


def _response(rating: TicketUserRating, db: Session):
    rated_by = db.query(User).filter(User.id == rating.rated_by_user_id).first()
    return {
        "ticket_id": rating.ticket_id,
        "rated_user_id": rating.rated_user_id,
        "rated_by_user_id": rating.rated_by_user_id,
        "rated_by_user_name": rated_by.name if rated_by else None,
        "rating": rating.rating,
        "reasons": rating.reasons or [],
        "comment": rating.comment,
        "created_at": rating.created_at,
    }


def get_user_rating(db: Session, ticket_id: int, current_user):
    """Estado de la calificación del usuario en un ticket: la que ya existe o si se puede calificar."""
    ticket = find_ticket_by_id(db, ticket_id)
    ensure_ticket_access(ticket, current_user)
    rating = db.query(TicketUserRating).filter(TicketUserRating.ticket_id == ticket_id).first()

    can_rate = (
        rating is None
        and ticket.status in RATEABLE_STATUSES
        and ticket.created_by_user_id is not None
        and (current_user.role == "admin" or ticket.assigned_to_user_id == current_user.id)
    )

    return {
        "rating": _response(rating, db) if rating else None,
        "can_rate": can_rate,
    }


def rate_user(db: Session, ticket_id: int, rating: int, reasons, comment, current_user):
    ticket = find_ticket_by_id(db, ticket_id)
    _ensure_can_rate(ticket, current_user)

    if ticket.status not in RATEABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Solo se califica al usuario cuando el ticket está resuelto, cerrado o cancelado"
        )

    if ticket.created_by_user_id is None:
        raise HTTPException(
            status_code=400,
            detail="El ticket no tiene usuario que calificar"
        )

    if db.query(TicketUserRating).filter(TicketUserRating.ticket_id == ticket_id).first():
        raise HTTPException(
            status_code=400,
            detail="Ya se calificó al usuario de este ticket"
        )

    reasons = list(dict.fromkeys(reasons or []))
    invalid = [r for r in reasons if r not in USER_RATING_REASONS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail="Motivo inválido"
        )

    record = TicketUserRating(
        ticket_id=ticket.id,
        rated_user_id=ticket.created_by_user_id,
        rated_by_user_id=current_user.id,
        rating=rating,
        reasons=reasons,
        comment=(comment or "").strip() or None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # El historial solo lo ve Soporte/Admin
    create_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="USER_RATING",
        old_value=None,
        new_value=str(rating)
    )

    return {"rating": _response(record, db), "can_rate": False}
