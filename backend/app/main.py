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
from models.notifyGroup import NotifyGroup
from routers.notifyGroupRouter import router as notify_group_router
from models.ticketSurvey import TicketSurvey
from models.notification import Notification
from models.passwordResetToken import PasswordResetToken
from routers.notificationRouter import router as notification_router
from security.jwt import SECRET_KEY
from services.scheduledJobs import start_scheduler, stop_scheduler





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
    # Confirmación/encuesta y cancelación (los tickets anteriores quedan en NULL: no piden encuesta)
    connection.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP"))
    connection.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP"))
    connection.execute(text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS cancel_reason TEXT"))
    connection.execute(text(
        "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS kind VARCHAR(30) NOT NULL DEFAULT 'ticket_update'"
    ))
    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP"))
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
    # Grupos de aviso iniciales (solo si la tabla está vacía; después se editan en Catálogos)
    connection.execute(text("""
        INSERT INTO notify_groups (key, name, emails)
        SELECT * FROM (VALUES
            ('infra', 'Infraestructura',
             ARRAY['sistemas3@empack.com.mx', 'sistemas2@empack.com.mx', 'sistemas4@empack.com.mx']::varchar[]),
            ('general', 'General',
             ARRAY['sistemas5@empack.com.mx', 'raul_jaramillo@empack.com.mx']::varchar[]),
            ('always', 'Siempre en copia',
             ARRAY['sistemas@empack.com.mx']::varchar[])
        ) AS seed(key, name, emails)
        WHERE NOT EXISTS (SELECT 1 FROM notify_groups)
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
app.include_router(notify_group_router,prefix=API_PREFIX)
app.include_router(notification_router,prefix=API_PREFIX)


# Cierre automático de tickets resueltos sin respuesta y limpieza de avisos viejos
@app.on_event("startup")
def on_startup():
    if SECRET_KEY == "CHANGE_THIS_SECRET_KEY":
        print("[SEGURIDAD] JWT_SECRET_KEY no está en el .env: cualquiera podría falsificar sesiones. "
              "Agrega una clave larga y aleatoria.")
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()

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