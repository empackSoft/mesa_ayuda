from fastapi import FastAPI
import os
from sqlalchemy import text
from database import engine, Base
from models.ticket import Ticket
from models.incidencia import Incidencia
from models.subincidencia import Subincidencia
from routers.ticketRouter import router as ticket_router
from routers.incidenciaRouter import router as incidencia_router
from models.user import User
from routers.userRouter import router as user_router
from routers.authRouter import router as auth_router
from models.ticketHistory import TicketHistory
from models.ticketAttachment import TicketAttachment
from models.ticketComment import TicketComment
from routers.dashboardRouter import router as dashboard_router
from models.location import Location
from routers.locationRouter import router as location_router





# CAMBIO PARA QUITAR ANTES DE USAR EN PRODUCCION
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false").lower() == "true"

# create_all no renombra ni agrega columnas a tablas que ya existen (no hay Alembic).
# Cambios de esquema pequeños e idempotentes (se pueden correr en cada arranque):

# 1) "branches" (sucursales) pasó a ser "locations" (ubicaciones: sucursal, CEDIS o corporativo).
#    Va antes de create_all para que no cree una tabla "locations" vacía.
with engine.begin() as connection:
    connection.execute(text("""
        DO $$
        BEGIN
            IF to_regclass('public.branches') IS NOT NULL AND to_regclass('public.locations') IS NULL THEN
                ALTER TABLE branches RENAME TO locations;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'users' AND column_name = 'branch_id') THEN
                ALTER TABLE users RENAME COLUMN branch_id TO location_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'tickets' AND column_name = 'branch_id') THEN
                ALTER TABLE tickets RENAME COLUMN branch_id TO location_id;
            END IF;
        END $$;
    """))

Base.metadata.create_all(bind=engine)

# 2) Columnas que faltan en tablas creadas con versiones anteriores del modelo
with engine.begin() as connection:
    connection.execute(text("""
        DO $$
        BEGIN
            -- Tipo de ubicación; al crearse se clasifican las existentes por su nombre
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name = 'locations' AND column_name = 'type') THEN
                ALTER TABLE locations ADD COLUMN type VARCHAR(20) NOT NULL DEFAULT 'branch';
                UPDATE locations SET type = 'cedis' WHERE name ILIKE 'cedis%';
                UPDATE locations SET type = 'corporate' WHERE name ILIKE 'corporativo%';
            END IF;
        END $$;
    """))
    connection.execute(text(
        "ALTER TABLE locations ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
    ))
    connection.execute(text("ALTER TABLE locations ALTER COLUMN code DROP NOT NULL"))
    connection.execute(text(
        "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS location_id INTEGER REFERENCES locations(id)"
    ))
    connection.execute(text("""
        DO $$
        BEGIN
            -- Grupo de aviso por correo; al crearse se marcan las categorías de infraestructura
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                           WHERE table_name = 'incidencias' AND column_name = 'notify_group') THEN
                ALTER TABLE incidencias ADD COLUMN notify_group VARCHAR(20) NOT NULL DEFAULT 'general';
                UPDATE incidencias SET notify_group = 'infra'
                WHERE name IN ('Hardware', 'Redes', 'Impresoras', 'Telefonía',
                               'Equipo de Cómputo', 'Biométrico');
            END IF;
        END $$;
    """))

app = FastAPI(
    title="Mesa Ayuda API",
    version="1.0.0",

    # CAMBIO PARA QUITAR ANTES DE USAR EN PRODUCCION
    docs_url="/mesa_ayuda/api/docs" if ENABLE_DOCS else None,
    openapi_url="/mesa_ayuda/api/openapi.json" if ENABLE_DOCS else None
)

# Si no existe la carpeta tickets la creamos.
# Los adjuntos NO se publican: solo se descargan por la API, que revisa permisos.
os.makedirs("uploads/tickets", exist_ok=True)

API_PREFIX = "/mesa_ayuda/api"


@app.get(API_PREFIX)
def root():
    return {
        "message": "Sistema Mesa de Ayuda EmPack activo"
    }


app.include_router(ticket_router,prefix=API_PREFIX)
app.include_router(incidencia_router,prefix=API_PREFIX)
app.include_router(user_router,prefix=API_PREFIX)
app.include_router(auth_router,prefix=API_PREFIX)
app.include_router(dashboard_router,prefix=API_PREFIX)
app.include_router(location_router,prefix=API_PREFIX)

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.get("/db-check")
def db_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "connected"
        }

    except Exception:
        # No se expone el detalle del error (puede incluir host/usuario de la BD)
        return {
            "database": "error"
        }