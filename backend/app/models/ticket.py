from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="open")

    branch_id = Column(Integer, ForeignKey("branches.id"))
    user_id = Column(Integer, ForeignKey("users.id"))