from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from datetime import datetime

from database import Base


# Aviso dentro del sistema (campanita). Se crea junto con cada correo de un ticket.
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=True
    )

    # Tipo crudo para el front (elige el sonido): "new_ticket" o "ticket_update"
    kind = Column(String(30), nullable=False, default="ticket_update")

    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )
