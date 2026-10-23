from datetime import datetime

from passlib.context import CryptContext
from fastapi import HTTPException


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="La contraseña no puede superar 72 bytes"
        )

    return pwd_context.hash(password)


def verify_password(
        plain_password: str,
        hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def set_user_password(user, password: str):
    """
    Única forma de cambiar una contraseña: guarda el hash y la fecha del cambio.
    Las sesiones emitidas antes de esa fecha dejan de valer (ver dependencies/auth.py).
    """
    user.password_hash = hash_password(password)
    user.password_changed_at = datetime.utcnow()
