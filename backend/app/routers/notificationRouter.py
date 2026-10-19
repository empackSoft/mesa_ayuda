from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import get_current_user
from models.user import User
from schemas.notification import NotificationList
from services.notificationService import (
    list_notifications,
    mark_read,
    mark_all_read
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get(
    "/",
    response_model=NotificationList
)
def get_notifications(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return list_notifications(db, current_user)


@router.patch("/read-all")
def read_all_notifications(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return mark_all_read(db, current_user)


@router.patch("/{notification_id}/read")
def read_notification(
        notification_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return mark_read(db, current_user, notification_id)
