from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db

from schemas.auth import (
    LoginRequest,
    LoginResponse
)

from services.authService import login_user
from dependencies.auth import get_current_user
from models.user import User


from dependencies.auth import get_current_user
from models.user import User


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    return login_user(
        db,
        login_data
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