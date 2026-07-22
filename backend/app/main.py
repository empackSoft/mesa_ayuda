from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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

# CAMBIO PARA QUITAR ANTES DE USAR EN PRODUCCION
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false").lower() == "true"

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mesa Ayuda API",
    version="1.0.0",

    # CAMBIO PARA QUITAR ANTES DE USAR EN PRODUCCION
    docs_url="/mesa_ayuda/api/docs" if ENABLE_DOCS else None,
    openapi_url="/mesa_ayuda/api/openapi.json" if ENABLE_DOCS else None
)

# Si no existe la carpeta tickets la creamos
os.makedirs("uploads/tickets", exist_ok=True)

# Publicamos archivos estaticos
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

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

    except Exception as e:
        return {
            "database": "error",
            "detail": str(e)
        }