from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import (
    require_admin,
    require_support_or_admin
)

from models.user import User

from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    StaffResponse
)

from services.userService import (
    create_user,
    get_users,
    get_staff_users,
    get_user_by_id,
    update_user,
    deactivate_user
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_user(
        user: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return create_user(
        db,
        user
    )


@router.get(
    "/",
    response_model=list[UserResponse]
)
def list_users(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return get_users(db)


# Soporte/admin activos, para elegir a quién asignar un ticket
@router.get(
    "/staff",
    response_model=list[StaffResponse]
)
def list_staff(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return get_staff_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return get_user_by_id(
        db,
        user_id
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse
)
def update_existing_user(
        user_id: int,
        user: UserUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return update_user(
        db,
        user_id,
        user,
        current_user
    )


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse
)
def deactivate_existing_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return deactivate_user(
        db,
        user_id,
        current_user
    )
