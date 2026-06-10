from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies.database import get_db

from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse
)

from services.userService import (
    create_user,
    get_users,
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
        db: Session = Depends(get_db)
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
        db: Session = Depends(get_db)
):
    return get_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
        user_id: int,
        db: Session = Depends(get_db)
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
        db: Session = Depends(get_db)
):
    return update_user(
        db,
        user_id,
        user
    )


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse
)
def deactivate_existing_user(
        user_id: int,
        db: Session = Depends(get_db)
):
    return deactivate_user(
        db,
        user_id
    )