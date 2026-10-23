import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.user import User
from models.passwordResetToken import PasswordResetToken
from schemas.auth import LoginRequest
from security import rateLimit
from security.password import verify_password, hash_password, set_user_password
from security.jwt import create_access_token
from services.emailService import send_email, FRONTEND_URL, FAKE_EMAIL_SUFFIX

# Fuerza bruta: tras 5 intentos fallidos con el mismo correo (o 30 desde la misma IP)
# en 15 minutos, se bloquea el login de ese correo/IP hasta que pase la ventana.
LOGIN_WINDOW = 15 * 60
MAX_FAILS_PER_EMAIL = 5
MAX_FAILS_PER_IP = 30

# "Olvidé mi contraseña": máximo 3 correos por hora a la misma cuenta
RESET_WINDOW = 60 * 60
MAX_RESETS_PER_EMAIL = 3
RESET_TOKEN_MINUTES = 60

# Hash de relleno: si el correo no existe se verifica contra él igual,
# para que la respuesta tarde lo mismo y no delate qué correos están registrados
_DUMMY_HASH = hash_password("relleno-para-tiempo-constante")


def _ensure_not_blocked(key: str, limit: int):
    if rateLimit.count_hits(key, LOGIN_WINDOW) >= limit:
        minutes = -(-rateLimit.retry_after(key, LOGIN_WINDOW) // 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intenta de nuevo en {minutes} minuto(s)."
        )


def login_user(
        db: Session,
        login_data: LoginRequest,
        client_ip: str = None
):
    email = login_data.email.strip().lower()
    email_key = f"login:email:{email}"
    ip_key = f"login:ip:{client_ip}"

    _ensure_not_blocked(email_key, MAX_FAILS_PER_EMAIL)
    if client_ip:
        _ensure_not_blocked(ip_key, MAX_FAILS_PER_IP)

    user = (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .first()
    )

    password_ok = verify_password(
        login_data.password,
        user.password_hash if user else _DUMMY_HASH
    )

    if user is None or not password_ok:
        rateLimit.register_hit(email_key, LOGIN_WINDOW)
        if client_ip:
            rateLimit.register_hit(ip_key, LOGIN_WINDOW)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    # Se revisa después de la contraseña: así no se puede averiguar qué cuentas existen
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    rateLimit.reset(email_key)

    return {
        "access_token": issue_token(user),
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


def issue_token(user: User) -> str:
    return create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    })


def change_own_password(
        db: Session,
        current_user: User,
        current_password: str,
        new_password: str
):
    key = f"password:user:{current_user.id}"
    _ensure_not_blocked(key, MAX_FAILS_PER_EMAIL)

    if not verify_password(current_password, current_user.password_hash):
        rateLimit.register_hit(key, LOGIN_WINDOW)
        raise HTTPException(
            status_code=400,
            detail="La contraseña actual no es correcta"
        )

    if current_password == new_password:
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe ser distinta de la actual"
        )

    rateLimit.reset(key)
    set_user_password(current_user, new_password)
    db.commit()

    # Las demás sesiones se cierran; esta recibe un token nuevo para seguir trabajando
    return {
        "message": "Contraseña actualizada",
        "access_token": issue_token(current_user)
    }


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def request_password_reset(db: Session, email: str):
    # Siempre la misma respuesta, exista o no la cuenta
    response = {
        "message": "Si el correo está registrado, te enviamos un link para restablecer tu contraseña."
    }

    email = email.strip().lower()
    key = f"reset:email:{email}"
    if rateLimit.register_hit(key, RESET_WINDOW) > MAX_RESETS_PER_EMAIL:
        return response

    user = (
        db.query(User)
        .filter(func.lower(User.email) == email)
        .first()
    )

    if user is None or user.is_active is False or user.email.lower().endswith(FAKE_EMAIL_SUFFIX):
        return response

    token = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(token),
        expires_at=datetime.utcnow() + timedelta(minutes=RESET_TOKEN_MINUTES)
    ))
    db.commit()

    link = f"{FRONTEND_URL}/restablecer-contrasena?token={token}"
    send_email(
        to=[user.email],
        subject="Restablecer tu contraseña",
        body=(
            f"Hola {user.name}:\n\n"
            f"Recibimos una solicitud para restablecer tu contraseña de la Mesa de Ayuda.\n\n"
            f"Abre este link para elegir una nueva (vence en {RESET_TOKEN_MINUTES} minutos):\n"
            f"{link}\n\n"
            f"Si no lo solicitaste, ignora este correo: tu contraseña no cambia.\n\n"
            f"Sistema Mesa de Ayuda EmPack"
        )
    )

    return response


def reset_password(db: Session, token: str, new_password: str):
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == _hash_token(token))
        .first()
    )

    if reset is None or reset.used_at is not None or reset.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="El link no es válido o ya venció. Solicita uno nuevo."
        )

    user = db.query(User).filter(User.id == reset.user_id).first()
    if user is None or user.is_active is False:
        raise HTTPException(
            status_code=400,
            detail="El link no es válido o ya venció. Solicita uno nuevo."
        )

    set_user_password(user, new_password)

    # El link es de un solo uso; también se invalidan los demás pendientes de esa cuenta
    now = datetime.utcnow()
    (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        )
        .update({PasswordResetToken.used_at: now})
    )
    db.commit()

    rateLimit.reset(f"login:email:{user.email.lower()}")

    return {"message": "Contraseña restablecida. Ya puedes iniciar sesión."}
