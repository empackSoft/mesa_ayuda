from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import require_admin, require_user_or_above

from schemas.location import LocationCreate, LocationUpdate, LocationResponse

from services import locationService

from models.user import User


router = APIRouter(
    prefix="/locations",
    tags=["Ubicaciones"]
)


@router.get(
    "/",
    response_model=list[LocationResponse]
)
def list_locations(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return locationService.get_locations(db)


@router.post(
    "/",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_location(
        location: LocationCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return locationService.create_location(db, location)


@router.put(
    "/{location_id}",
    response_model=LocationResponse
)
def update_existing_location(
        location_id: int,
        location: LocationUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return locationService.update_location(db, location_id, location)
