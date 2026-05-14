from fastapi import FastAPI

app = FastAPI(title="Ticket System API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Sistema activo"}







