from sqlalchemy.orm import Session

from models.ticket import Ticket
from schemas.ticket import TicketCreate


def create_ticket(db: Session, ticket: TicketCreate):

    new_ticket = Ticket(
        title=ticket.title,
        status=ticket.status,
        priority=ticket.priority
    )

    db.add(new_ticket)

    db.commit()

    db.refresh(new_ticket)

    return new_ticket


def get_tickets(db: Session):

    return db.query(Ticket).all()