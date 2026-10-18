import re

from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.notifyGroup import NotifyGroup
from schemas.notifyGroup import NotifyGroupUpdate

# Grupo que va en copia en todos los tickets (no se asigna a categorías)
ALWAYS_GROUP = "always"

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_notify_groups(db: Session):
    return (
        db.query(NotifyGroup)
        .order_by(NotifyGroup.id.asc())
        .all()
    )


def get_notify_group_by_id(db: Session, group_id: int):
    group = (
        db.query(NotifyGroup)
        .filter(NotifyGroup.id == group_id)
        .first()
    )

    if not group:
        raise HTTPException(
            status_code=404,
            detail="Grupo de aviso no encontrado"
        )

    return group


def get_group_emails(db: Session, key: str) -> list:
    group = (
        db.query(NotifyGroup)
        .filter(NotifyGroup.key == key)
        .first()
    )

    return list(group.emails) if group else []


def get_all_group_emails(db: Session) -> list:
    return [email for group in get_notify_groups(db) for email in group.emails]


def validate_category_group(db: Session, key: str):
    exists = (
        db.query(NotifyGroup)
        .filter(NotifyGroup.key == key, NotifyGroup.key != ALWAYS_GROUP)
        .first()
    )

    if not exists:
        raise HTTPException(
            status_code=400,
            detail="Grupo de aviso inválido"
        )


def update_notify_group(db: Session, group_id: int, group_data: NotifyGroupUpdate):
    group = get_notify_group_by_id(db, group_id)

    data = group_data.model_dump(exclude_unset=True)

    if "name" in data:
        group.name = data["name"].strip()

    if "emails" in data:
        emails = []
        for email in data["emails"]:
            email = email.strip().lower()
            if not EMAIL_PATTERN.match(email):
                raise HTTPException(
                    status_code=400,
                    detail=f"Correo inválido: {email}"
                )
            if email not in emails:
                emails.append(email)
        group.emails = emails

    db.commit()
    db.refresh(group)

    return group
