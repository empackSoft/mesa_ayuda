from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import require_admin

from schemas.notifyGroup import NotifyGroupUpdate, NotifyGroupResponse

from services import notifyGroupService

from models.user import User


router = APIRouter(
    prefix="/notify-groups",
    tags=["Grupos de aviso"]
)


@router.get(
    "/",
    response_model=list[NotifyGroupResponse]
)
def list_notify_groups(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return notifyGroupService.get_notify_groups(db)


@router.put(
    "/{group_id}",
    response_model=NotifyGroupResponse
)
def update_existing_notify_group(
        group_id: int,
        group: NotifyGroupUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return notifyGroupService.update_notify_group(db, group_id, group)
