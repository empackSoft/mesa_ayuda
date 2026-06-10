from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from dependencies.database import get_db

from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse
)

from services.ticketService import (
    create_ticket,
    get_tickets,
    get_ticket_by_id,
    update_ticket,
    close_ticket,
    delete_ticket
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_ticket(
        ticket: TicketCreate,
        db: Session = Depends(get_db)
):
    return create_ticket(db, ticket)


@router.get(
    "/",
    response_model=list[TicketResponse]
)
def list_tickets(
        db: Session = Depends(get_db)
):
    return get_tickets(db)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
        ticket_id: int,
        db: Session = Depends(get_db)
):
    return get_ticket_by_id(db, ticket_id)


@router.put(
    "/{ticket_id}",
    response_model=TicketResponse
)
def update_existing_ticket(
        ticket_id: int,
        ticket: TicketUpdate,
        db: Session = Depends(get_db)
):
    return update_ticket(db, ticket_id, ticket)


@router.patch(
    "/{ticket_id}/close",
    response_model=TicketResponse
)
def close_existing_ticket(
        ticket_id: int,
        db: Session = Depends(get_db)
):
    return close_ticket(db, ticket_id)


@router.delete("/{ticket_id}")
def delete_existing_ticket(
        ticket_id: int,
        db: Session = Depends(get_db)
):
    return delete_ticket(db, ticket_id)