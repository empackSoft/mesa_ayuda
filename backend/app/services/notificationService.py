from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.notification import Notification
from models.user import User

# Los avisos leídos se borran solos después de este tiempo (ver scheduledJobs)
KEEP_READ_DAYS = 90


def create_notifications(
        db: Session,
        emails: list,
        ticket_id: int,
        title: str,
        body: str,
        exclude_user_id: int = None,
        kind: str = "ticket_update",
        include_all_staff: bool = False
):
    """
    Un aviso por cada usuario activo cuyo correo esté en `emails`
    (los mismos destinatarios que el correo del evento), menos quien hizo la acción.
    Con include_all_staff, además a todo el personal activo de soporte y admin.
    """
    emails = {e.strip().lower() for e in emails if e}
    if not emails and not include_all_staff:
        return

    conditions = [func.lower(User.email).in_(emails)] if emails else []
    if include_all_staff:
        conditions.append(User.role.in_(["support", "admin"]))

    users = (
        db.query(User.id)
        .filter(
            or_(*conditions),
            User.is_active == True
        )
        .all()
    )

    for (user_id,) in users:
        if user_id == exclude_user_id:
            continue
        db.add(Notification(
            user_id=user_id,
            ticket_id=ticket_id,
            kind=kind,
            title=title[:200],
            body=body
        ))

    db.commit()


def list_notifications(db: Session, current_user: User, limit: int = 20):
    items = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.id.desc())
        .limit(limit)
        .all()
    )

    unread_count = (
        db.query(func.count(Notification.id))
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .scalar()
    )

    return {
        "unread_count": unread_count,
        "items": items
    }


def mark_read(db: Session, current_user: User, notification_id: int):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Aviso no encontrado"
        )

    notification.is_read = True
    db.commit()

    return {"message": "Aviso leído"}


def mark_all_read(db: Session, current_user: User):
    (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .update({Notification.is_read: True})
    )
    db.commit()

    return {"message": "Avisos leídos"}


def purge_old_notifications(db: Session):
    limit = datetime.utcnow() - timedelta(days=KEEP_READ_DAYS)
    (
        db.query(Notification)
        .filter(
            Notification.is_read == True,
            Notification.created_at < limit
        )
        .delete()
    )
    db.commit()
