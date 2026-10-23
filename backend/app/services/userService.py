from schemas.user import UserCreate, UserUpdate
from security.password import hash_password, set_user_password
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.user import User
from models.location import Location

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


def ensure_location_exists(db: Session, location_id):
    if location_id is None:
        return

    if not db.query(Location).filter(Location.id == location_id).first():
        raise HTTPException(
            status_code=400,
            detail="La ubicación no existe"
        )


# Los tickets toman la ubicación de quien los levanta, así que un "user" siempre debe tener una
def ensure_user_has_location(role, location_id):
    if role == "user" and location_id is None:
        raise HTTPException(
            status_code=400,
            detail="Asigna una ubicación al usuario: sus tickets se registran con ella"
        )


def create_user(
        db: Session,
        user_data: UserCreate
):
    ensure_location_exists(db, user_data.location_id)
    ensure_user_has_location(user_data.role, user_data.location_id)

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
        location_id=user_data.location_id,
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

    if "location_id" in data:
        ensure_location_exists(db, data["location_id"])

    # Solo se valida si se toca el rol o la ubicación (los usuarios importados sin
    # ubicación se pueden seguir editando hasta que se les asigne una)
    if "location_id" in data or "role" in data:
        ensure_user_has_location(
            data.get("role", user.role),
            data.get("location_id", user.location_id)
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
        set_user_password(user, data.pop("password"))

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