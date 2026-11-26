from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from models.department import Department
from schemas.department import DepartmentCreate, DepartmentUpdate


# Catálogo inicial (se carga solo si la tabla está vacía; después se edita en Catálogos)
INITIAL_DEPARTMENTS = [
    "Contabilidad", "CxC", "CxP", "Tesorería", "Costos", "Crédito y Cobranza", "Almacén",
    "Tráfico", "Sistemas", "Ventas Corporativas", "Ventas Mayoreo", "Punto de Venta",
    "Tienda Virtual", "Diseño", "Recursos Humanos", "Mantenimiento", "Dirección General",
    "Dirección Comercial", "Franquicia", "Externo", "Producción", "Cobranza", "Auditoría",
    "Soporte Dirección",
]


def seed_departments(db: Session):
    if db.query(Department).first() is None:
        db.add_all(Department(name=name, is_active=True) for name in INITIAL_DEPARTMENTS)
        db.commit()


def get_departments(db: Session):
    return db.query(Department).order_by(Department.name.asc()).all()


def get_department_by_id(db: Session, department_id: int):
    department = db.query(Department).filter(Department.id == department_id).first()

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Departamento no encontrado"
        )

    return department


def _ensure_unique_name(db: Session, name: str, exclude_id: int = None):
    query = db.query(Department).filter(func.lower(Department.name) == name.lower())

    if exclude_id is not None:
        query = query.filter(Department.id != exclude_id)

    if query.first():
        raise HTTPException(
            status_code=400,
            detail="El departamento ya existe"
        )


def create_department(db: Session, data: DepartmentCreate):
    name = data.name.strip()
    _ensure_unique_name(db, name)

    department = Department(name=name, is_active=True)
    db.add(department)
    db.commit()
    db.refresh(department)

    return department


def update_department(db: Session, department_id: int, data: DepartmentUpdate):
    department = get_department_by_id(db, department_id)
    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        changes["name"] = changes["name"].strip()
        _ensure_unique_name(db, changes["name"], exclude_id=department_id)

    for field, value in changes.items():
        setattr(department, field, value)

    db.commit()
    db.refresh(department)

    return department
