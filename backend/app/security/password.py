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