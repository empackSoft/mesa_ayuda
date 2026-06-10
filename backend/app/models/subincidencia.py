from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Subincidencia(Base):
    __tablename__ = "subincidencias"

    id = Column(Integer, primary_key=True, index=True)
    incidencia_id = Column(Integer, ForeignKey("incidencias.id"), nullable=False)

    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

    incidencia = relationship(
        "Incidencia",
        back_populates="subincidencias"
    )