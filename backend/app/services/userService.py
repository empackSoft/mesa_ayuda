from schemas.user import UserCreate, UserUpdate
from security.password import hash_password
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User

VALID_ROLES = [
    "user",
    "support",
    "admin"
]


def get_users(db: Session):
    return (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )


def get_staff_users(db: Session):
    return (
        db.query(User)
        .filter(
            User.role.in_(["support", "admin"]),
            User.is_active == True
        )
        .order_by(User.name.asc())
        .all()
    )


def get_user_by_id(
        db: Session,
        user_id: int
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return user


def get_user_by_email(
        db: Session,
        email: str
):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def create_user(
        db: Session,
        user_data: UserCreate
):
    if user_data.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Rol inválido"
        )

    existing_user = get_user_by_email(
        db,
        user_data.email
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="El correo ya está registrado"
        )

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        branch_id=user_data.branch_id,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
        db: Session,
        user_id: int,
        user_data: UserUpdate,
        current_user=None
):
    user = get_user_by_id(
        db,
        user_id
    )

    data = user_data.model_dump(exclude_unset=True)

    # Un admin no puede quitarse su rol ni desactivarse (evita quedarse sin administradores)
    if current_user is not None and current_user.id == user.id:
        if "role" in data and data["role"] != user.role:
            raise HTTPException(
                status_code=400,
                detail="No puedes cambiar tu propio rol"
            )

        if data.get("is_active") is False:
            raise HTTPException(
                status_code=400,
                detail="No puedes desactivar tu propia cuenta"
            )

    if "role" in data and data["role"] not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Rol inválido"
        )

    if "email" in data:
        existing_user = get_user_by_email(
            db,
            data["email"]
        )

        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=400,
                detail="El correo ya está registrado"
            )

    if "password" in data:
        user.password_hash = hash_password(data["password"])
        data.pop("password")

    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


def deactivate_user(
        db: Session,
        user_id: int,
        current_user=None
):
    user = get_user_by_id(
        db,
        user_id
    )

    if current_user is not None and current_user.id == user.id:
        raise HTTPException(
            status_code=400,
            detail="No puedes desactivar tu propia cuenta"
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="El usuario ya está inactivo"
        )

    user.is_active = False

    db.commit()
    db.refresh(user)

    return user