from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime

from database import Base


# Calificación que Soporte le da al usuario que levantó el ticket (la otra cara de la encuesta):
# si respondió, si la información era correcta, etc. Solo la ve Soporte/Admin, nunca el usuario.
# Una por ticket y no se edita (auditoría).
class TicketUserRating(Base):
    __tablename__ = "ticket_user_ratings"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, unique=True)

    # A quién se califica (quien levantó el ticket) y quién califica (técnico o admin)
    rated_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    rated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    rating = Column(Integer, nullable=False)
    # Motivos crudos (USER_RATING_REASONS en ticketUserRatingService); el front los traduce
    reasons = Column(ARRAY(String(30)), nullable=False, default=list)
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
