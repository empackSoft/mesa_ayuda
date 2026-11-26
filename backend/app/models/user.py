from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)

    password_hash = Column(String(255), nullable=False)

    # Último cambio de contraseña: las sesiones emitidas antes dejan de valer
    password_changed_at = Column(DateTime, nullable=True)

    role = Column(String(50), nullable=False, default="user")

    # Ubicación del usuario; sus tickets se registran con ella
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    # Departamento (catálogo). Obligatorio al dar de alta; los importados pueden no tenerlo aún
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

# Para que las llaves foráneas resuelvan aunque un script solo importe User
from models.location import Location  # noqa: E402,F401
from models.department import Department  # noqa: E402,F401
