from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


# Encuesta de satisfacción (obligatoria) de un ticket resuelto o cerrado.
# Si el usuario no la contesta en 24 h se llena sola con 5 estrellas (is_auto=True).
class TicketSurvey(Base):
    __tablename__ = "ticket_surveys"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False,
        unique=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    is_auto = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="survey")
