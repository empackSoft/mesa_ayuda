from fastapi import APIRouter
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal
from schemas.ticket import TicketCreate, TicketResponse
from services.ticketService import create_ticket, get_tickets

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

# RUTA PRINCIPAL PARA HACER SOLICITUDES DE LA MESA DE AYUDA
@router.post("/", response_model=TicketResponse)
def create(ticket: TicketCreate):

    db: Session = SessionLocal()

    try:
        return create_ticket(db, ticket)

    finally:
        db.close()

# RUTA PRINCIPAL PARA VISITAR EL SITIO PARA LA MESA DE AYUDA
@router.get("/", response_model=List[TicketResponse])
def list_all():

    db: Session = SessionLocal()

    try:
        return get_tickets(db)

    finally:
        db.close()