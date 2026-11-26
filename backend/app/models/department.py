from sqlalchemy import Column, Integer, String, Boolean

from database import Base


# Departamento de EmPack (Contabilidad, Sistemas, Ventas...). Cada usuario pertenece a uno.
# No se borra: se desactiva, para no dejar usuarios sin departamento.
class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
