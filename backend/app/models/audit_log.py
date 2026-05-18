from sqlalchemy import Column, Integer, String
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    username = Column(String)
    ip_address = Column(String)
