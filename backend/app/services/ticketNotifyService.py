from sqlalchemy.orm import Session

from models.ticket import Ticket
from services.emailService import send_email, build_ticket_link
from services.notificationService import create_notifications
from services.notifyGroupService import ALWAYS_GROUP, get_group_emails, get_all_group_emails

# Avisos por correo de un ticket: UN solo correo por evento.
# - Para: quien levantó el ticket (salvo en notas internas).
# - CC, antes de asignarse: todos los grupos de aviso.
# - CC, ya asignado: el grupo de la categoría + el técnico asignado.
# - CC siempre: el grupo "Siempre en copia".
# Los grupos y sus correos están en la tabla notify_groups (se editan en Catálogos).
# Los mismos destinatarios que tienen cuenta reciben además el aviso de la campanita.

STATUS_LABELS = {
    "open": "Abierto",
    "in_progress": "En progreso",
    "pending": "Pendiente",
    "resolved": "Resuelto",
    "closed": "Cerrado",
    "cancelled": "Cancelado",
}

# Va en el correo de creación: el usuario debe saber desde el inicio cómo se cierra su ticket
CLOSING_POLICY = (
    "Importante: cuando Soporte marque tu ticket como resuelto, te pediremos confirmar "
    "que quedó solucionado y calificar la atención (encuesta obligatoria). "
    "Si no respondes en 24 horas, el ticket se cerrará automáticamente "
    "y la encuesta se registrará con 5 estrellas, sin comentarios."
)


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
        include_creator: bool = True,
        actor=None,
        footer: str = None,
        kind: str = "ticket_update"
):
    creator = ticket.created_by
    to = [creator.email] if include_creator and creator and creator.email else []
    cc = staff_recipients(db, ticket)

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
        + (f"{footer}\n\n" if footer else "")
        + "Sistema Mesa de Ayuda EmPack"
    )

    send_email(
        to=to,
        cc=cc,
        subject=f"Ticket #{ticket.id} · {subject}",
        body=body
    )

    # Campanita: quien hizo la acción no se avisa a sí mismo.
    # Mientras nadie lo tenga asignado, le llega a todo soporte/admin (estén o no en un grupo),
    # para que cualquiera pueda tomarlo.
    create_notifications(
        db,
        emails=to + cc,
        ticket_id=ticket.id,
        title=f"Ticket #{ticket.id} · {subject}",
        body=message[:300],
        exclude_user_id=actor.id if actor else None,
        kind=kind,
        include_all_staff=ticket.assigned_to_user_id is None
    )
