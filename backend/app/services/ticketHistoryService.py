from sqlalchemy.orm import Session
from models.ticketHistory import TicketHistory
from fastapi import HTTPException
from models.user import User



def create_history(
        db: Session,
        ticket_id: int,
        user_id: int | None,
        action: str,
        old_value: str | None,
        new_value: str | None
):
    print("========== CREATE_HISTORY ==========")
    history = TicketHistory(
        ticket_id=ticket_id,
        user_id=user_id,
        action=action,
        old_value=old_value,
        new_value=new_value
    )

    db.add(history)
    db.commit()
    db.refresh(history)
    # print("========== HISTORY OK ==========")
    return history

def build_history_message(
        db: Session,
        action,
        old_value,
        new_value
):

    if action == "CREATE":
        return "Ticket creado"

    elif action == "ASSIGN":

        user_name = get_user_name(
            db,
            int(new_value)
        )

        return f"Ticket asignado a {user_name}"

    elif action == "STATUS":
        return f"Estado cambiado de '{old_value}' a '{new_value}'"

    elif action == "UPDATE_PRIORITY":
        return f"Prioridad cambiada de '{old_value}' a '{new_value}'"

    elif action == "UPDATE_DESCRIPTION":
        return "Se modificó la descripción del ticket"

    elif action == "CLOSE":
        return "Ticket cerrado"

    return action


def get_ticket_history(
        db: Session,
        ticket_id: int
):
    history = (
        db.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
        .all()
    )

    if not history:
        raise HTTPException(
            status_code=404,
            detail="No existe historial para este ticket"
        )

    result = []

    for item in history:

        user = None

        if item.user_id:

            user = (
                db.query(User)
                .filter(User.id == item.user_id)
                .first()
            )

        result.append(
            {
                "id": item.id,
                "ticket_id": item.ticket_id,

                "user_id": item.user_id,
                "user_name": user.name if user else None,
                "user_role": user.role if user else None,

                "action": item.action,
                "message": build_history_message(
                    db,
                    item.action,
                    item.old_value,
                    item.new_value
                ),

                "old_value": item.old_value,
                "new_value": item.new_value,

                "created_at": item.created_at
            }
        )

    return result


def get_user_name(db: Session, user_id: int):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    return user.name if user else f"Usuario {user_id}"