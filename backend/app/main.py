from fastapi import FastAPI
from sqlalchemy import text
from database import engine, Base
from models.ticket import Ticket
from models.incidencia import Incidencia
from models.subincidencia import Subincidencia
from routers.ticketRouter import router as ticket_router
from routers.incidenciaRouter import router as incidencia_router
from models.user import User
from routers.userRouter import router as user_router


Base.metadata.create_all(bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mesa Ayuda API",
    version="1.0.0"
)

API_PREFIX = "/mesa_ayuda/api"


@app.get(API_PREFIX)
def root():
    return {
        "message": "Sistema Mesa de Ayuda EmPack activo"
    }


app.include_router(
    ticket_router,
    prefix=API_PREFIX
)

app.include_router(
    incidencia_router,
    prefix=API_PREFIX
)

app.include_router(
    user_router,
    prefix=API_PREFIX
)

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