import os

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from dependencies.database import get_db
from security.jwt import decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User


# La sesión del navegador viaja en una cookie httpOnly (JavaScript no puede leerla,
# así un XSS no puede robarla). Los scripts y pruebas pueden seguir usando "Authorization: Bearer".
SESSION_COOKIE = "mesa_session"
COOKIE_PATH = "/mesa_ayuda"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

# Con la cookie, toda petición que modifica algo debe traer este encabezado. Un sitio ajeno
# no puede agregarlo a un formulario, así que bloquea CSRF (además de SameSite=Strict).
CSRF_HEADER = "x-requested-with"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

security = HTTPBearer(auto_error=False)


def set_session_cookie(response, token: str):
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict"
    )


def clear_session_cookie(response):
    response.delete_cookie(
        key=SESSION_COOKIE,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict"
    )


def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
):
    if credentials is not None:
        token = credentials.credentials
    else:
        token = request.cookies.get(SESSION_COOKIE)
        if token and request.method not in SAFE_METHODS and not request.headers.get(CSRF_HEADER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solicitud no permitida"
            )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No has iniciado sesión"
        )

    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    # Sesión emitida antes del último cambio de contraseña: ya no vale
    if user.password_changed_at is not None and payload["iat"] < int(user.password_changed_at.timestamp()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tu contraseña cambió. Vuelve a iniciar sesión."
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    return user


def require_admin(
        current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )

    return current_user


def require_support_or_admin(
        current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["support", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de soporte"
        )

    return current_user


def require_user_or_above(
        current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["user", "support", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos"
        )

    return current_user
