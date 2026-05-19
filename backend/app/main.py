from fastapi import FastAPI
from sqlalchemy import text

from database import engine
from routers.ticketRouter import router as ticket_router

app = FastAPI(
    title="Mesa Ayuda API"
)

API_PREFIX = "/mesa_ayuda/api"

app.include_router(
    ticket_router,
    prefix=API_PREFIX
)


@app.get("/")
def root():
    return {"message": "Sistema activo"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():

    try:

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"database": "connected"}

    except Exception as e:
        return {"error": str(e)}