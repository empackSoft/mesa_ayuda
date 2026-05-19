from sqlalchemy import Column, Integer, String
from models.base import Base

class Ticket(Base):

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    status = Column(String, nullable=False)

    priority = Column(String, nullable=False)