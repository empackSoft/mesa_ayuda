from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    incidencia_id = Column(
        Integer,
        ForeignKey("incidencias.id"),
        nullable=False
    )

    subincidencia_id = Column(
        Integer,
        ForeignKey("subincidencias.id"),
        nullable=False
    )

    description = Column(Text, nullable=False)
    attachment_path = Column(String(255), nullable=True)

    status = Column(String(50), nullable=False, default="open")
    priority = Column(String(50), nullable=False, default="medium")

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    incidencia = relationship("Incidencia")
    subincidencia = relationship("Subincidencia")