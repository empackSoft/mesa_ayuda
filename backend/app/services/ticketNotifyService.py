from sqlalchemy.orm import Session

from models.ticket import Ticket
from services.emailService import send_email, build_ticket_link
from services.notifyGroupService import ALWAYS_GROUP, get_group_emails, get_all_group_emails

# Avisos por correo de un ticket: UN solo correo por evento.
# - Para: quien levantó el ticket (salvo en notas internas).
# - CC, antes de asignarse: todos los grupos de aviso.
# - CC, ya asignado: el grupo de la categoría + el técnico asignado.
# - CC siempre: el grupo "Siempre en copia".
# Los grupos y sus correos están en la tabla notify_groups (se editan en Catálogos).

STATUS_LABELS = {
    "open": "Abierto",
    "in_progress": "En progreso",
    "pending": "Pendiente",
    "resolved": "Resuelto",
    "closed": "Cerrado",
}


def staff_recipients(db: Session, ticket: Ticket) -> list:
    if ticket.assigned_to_user_id is None:
        return get_all_group_emails(db)

    group = ticket.incidencia.notify_group if ticket.incidencia else "general"
    emails = get_group_emails(db, group)
    if ticket.assigned_to and ticket.assigned_to.email:
        emails.append(ticket.assigned_to.email)

    return emails + get_group_emails(db, ALWAYS_GROUP)


def notify_ticket(
        db: Session,
        ticket: Ticket,
        subject: str,
        message: str,
        include_creator: bool = True
):
    creator = ticket.created_by
    to = [creator.email] if include_creator and creator and creator.email else []

    body = (
        f"{message}\n\n"
        f"Ticket: #{ticket.id}\n"
        f"Levantado por: {creator.name if creator else '—'}\n"
        f"Ubicación: {ticket.location.name if ticket.location else '—'}\n"
        f"Categoría: {ticket.incidencia.name if ticket.incidencia else '—'}"
        f" / {ticket.subincidencia.name if ticket.subincidencia else '—'}\n"
        f"Asignado a: {ticket.assigned_to.name if ticket.assigned_to else 'Sin asignar'}\n"
        f"Estado: {STATUS_LABELS.get(ticket.status, ticket.status)}\n\n"
        f"Descripción:\n{ticket.description}\n\n"
        f"Puedes verlo aquí: {build_ticket_link(ticket.id)}\n\n"
        f"Sistema Mesa de Ayuda EmPack"
    )

    send_email(
        to=to,
        cc=staff_recipients(db, ticket),
        subject=f"Ticket #{ticket.id} · {subject}",
        body=body
    )
