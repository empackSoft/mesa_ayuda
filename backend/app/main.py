from fastapi import FastAPI
from sqlalchemy import text
from database import engine

app = FastAPI(
    title="Mesa Ayuda API"
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


@app.get("/create-test")
def create_test():
    from models.base import Base
    Base.metadata.create_all(bind=engine)
    return {"tables": "created"}