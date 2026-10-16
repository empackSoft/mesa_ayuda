from sqlalchemy import Column, Integer, String, Boolean

from database import Base


# Ubicación de EmPack: sucursal, CEDIS o corporativo (ver LOCATION_TYPES en locationService).
# Los usuarios pertenecen a una y cada ticket guarda la ubicación desde donde se levantó.
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)
    type = Column(String(20), nullable=False, default="branch")
    code = Column(String(50), unique=True, nullable=True)
    city = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
