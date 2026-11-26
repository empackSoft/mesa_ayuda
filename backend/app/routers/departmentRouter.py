from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies.database import get_db
from dependencies.auth import require_admin, require_support_or_admin

from schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse

from services import departmentService

from models.user import User


router = APIRouter(
    prefix="/departments",
    tags=["Departamentos"]
)


@router.get(
    "/",
    response_model=list[DepartmentResponse]
)
def list_departments(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return departmentService.get_departments(db)


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_department(
        department: DepartmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return departmentService.create_department(db, department)


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse
)
def update_existing_department(
        department_id: int,
        department: DepartmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return departmentService.update_department(db, department_id, department)
