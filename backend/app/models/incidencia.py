from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    # Key del grupo de soporte al que avisa por correo (tabla notify_groups)
    notify_group = Column(String(20), nullable=False, default="general", server_default="general")

    subincidencias = relationship(
        "Subincidencia",
        back_populates="incidencia"
    )