from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from dependencies.database import get_db

from dependencies.auth import (
    require_admin,
    require_support_or_admin,
    require_user_or_above
)

from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketResponse
)

from services.ticketService import (
    create_ticket,
    get_tickets,
    get_ticket_by_id,
    update_ticket,
    close_ticket,
    delete_ticket,
    assign_ticket
)

from models.user import User


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
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return create_ticket(
        db,
        ticket,
        current_user
    )

@router.get(
    "/",
    response_model=list[TicketResponse]
)
def list_tickets(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        incidencia_id: Optional[int] = None,
        subincidencia_id: Optional[int] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_user_or_above)
):
    return get_tickets(
        db=db,
        status=status,
        priority=priority,
        incidencia_id=incidencia_id,
        subincidencia_id=subincidencia_id,
        created_from=created_from,
        created_to=created_to,
        current_user=current_user
    )

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse
)
def get_ticket(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return get_ticket_by_id(
        db,
        ticket_id
    )

@router.put(
    "/{ticket_id}",
    response_model=TicketResponse
)
def update_existing_ticket(
        ticket_id: int,
        ticket: TicketUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return update_ticket(
        db,
        ticket_id,
        ticket
    )

@router.patch(
    "/{ticket_id}/close",
    response_model=TicketResponse
)
def close_existing_ticket(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return close_ticket(
        db,
        ticket_id
    )


@router.delete("/{ticket_id}")
def delete_existing_ticket(
        ticket_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    return delete_ticket(
        db,
        ticket_id
    )

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse
)
def assign_existing_ticket(
        ticket_id: int,
        assign_data: TicketAssign,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_support_or_admin)
):
    return assign_ticket(
        db=db,
        ticket_id=ticket_id,
        assigned_to_user_id=assign_data.assigned_to_user_id
    )