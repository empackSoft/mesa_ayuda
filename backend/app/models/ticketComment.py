from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    body = Column(Text, nullable=False)
    is_internal = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User")