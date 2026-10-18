from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY

from database import Base


# Grupo de aviso por correo. Cada categoría (incidencias.notify_group) apunta a uno por su key.
# El grupo "always" no se elige en categorías: va en copia en TODOS los tickets.
class NotifyGroup(Base):
    __tablename__ = "notify_groups"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    emails = Column(ARRAY(String(150)), nullable=False, default=list)
