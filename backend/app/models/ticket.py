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

    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    assigned_to_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    description = Column(Text, nullable=False)


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

    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id]
    )

    assigned_to = relationship(
        "User",
        foreign_keys=[assigned_to_user_id]
    )

    attachments = relationship(
        "TicketAttachment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )

    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )