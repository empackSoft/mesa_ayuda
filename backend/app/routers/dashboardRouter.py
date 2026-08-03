from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import require_support_or_admin
from services.dashboardService import get_dashboard
from models.user import User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/")
def read_dashboard(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return get_dashboard(db=db)