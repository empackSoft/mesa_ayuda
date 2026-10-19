from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from dependencies.database import get_db

from schemas.auth import (
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)

from services.authService import (
    login_user,
    change_own_password,
    request_password_reset,
    reset_password
)
from dependencies.auth import get_current_user
from models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


def client_ip(request: Request):
    # Detrás de Apache + nginx: la IP real viene en X-Forwarded-For (la primera)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("x-real-ip") or (request.client.host if request.client else None)


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
        login_data: LoginRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    return login_user(
        db,
        login_data,
        client_ip(request)
    )


@router.get("/me")
def me(
        current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


@router.put("/password")
def change_password(
        data: ChangePasswordRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return change_own_password(
        db,
        current_user,
        data.current_password,
        data.new_password
    )


@router.post("/forgot-password")
def forgot_password(
        data: ForgotPasswordRequest,
        db: Session = Depends(get_db)
):
    return request_password_reset(db, data.email)


@router.post("/reset-password")
def reset_forgotten_password(
        data: ResetPasswordRequest,
        db: Session = Depends(get_db)
):
    return reset_password(db, data.token, data.new_password)
