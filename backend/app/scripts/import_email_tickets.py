"""
Carga los tickets que llegaron por correo mientras el sistema no estaba disponible.

Lee una carpeta con:
    tickets_correos.json   lista de tickets (ver el ejemplo en SISTEMA_SOPORTE/correos_caida/carga)
    <adjuntos>             los archivos que nombra cada ticket en "attachments"

Uso (dentro del contenedor backend; antes copiar la carpeta, p. ej. a /tmp/carga):
    python scripts/import_email_tickets.py /tmp/carga            # solo muestra qué cargaría
    python scripts/import_email_tickets.py /tmp/carga --aplicar  # crea los tickets

Si el correo es de un ticket que ya existe en el sistema anterior, se pone "folio" (p. ej.
"EK47N3558"): en vez de crear otro ticket, se agregan al importado el correo como comentario,
los adjuntos, los comentarios y el técnico (si no tenía).

Se puede correr varias veces: un ticket ya cargado (mismo asunto) se omite.
No manda correos ni avisos. Los correos se normalizan a @empack.com.mx.
Los tickets cerrados no piden encuesta (igual que los importados del sistema anterior).
"""
import json
import os
import secrets
import shutil
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal  # noqa: E402
from models.user import User  # noqa: E402
from models.location import Location  # noqa: E402
from models.incidencia import Incidencia  # noqa: E402
from models.subincidencia import Subincidencia  # noqa: E402
from models.ticket import Ticket  # noqa: E402
from models.ticketHistory import TicketHistory  # noqa: E402
from models.ticketComment import TicketComment  # noqa: E402
from models.ticketAttachment import TicketAttachment  # noqa: E402
from security.password import hash_password  # noqa: E402
from scripts.import_legacy import key, normalize_email  # noqa: E402

EMAIL_MARK = "— Recibido por correo durante la caída del sistema"
UPLOAD_FOLDER = "uploads/tickets"  # igual que ticketService (relativo a /app)
VALID_STATUS = {"open", "in_progress", "pending", "closed"}


def to_utc(value):
    """'2026-10-26T12:25:58-06:00' -> datetime UTC sin zona (como guarda la app)."""
    return datetime.fromisoformat(value).astimezone(timezone.utc).replace(tzinfo=None)


def mark(subject):
    return f"{EMAIL_MARK} (asunto: {subject})"


def add_attachments_and_comments(db, folder, it, ticket, requester, users):
    created = to_utc(it["received_at"])
    for name in it.get("attachments", []):
        path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{os.path.splitext(name)[1].lower()}")
        shutil.copyfile(os.path.join(folder, name), path)
        db.add(TicketAttachment(ticket_id=ticket.id, file_path=path, original_name=name,
                                uploaded_by=requester.id, created_at=created))
        db.add(TicketHistory(ticket_id=ticket.id, user_id=requester.id, action="UPLOAD_ATTACHMENT",
                             old_value=None, new_value=path, created_at=created))
    for c in it.get("comments", []):
        db.add(TicketComment(ticket_id=ticket.id, user_id=users[normalize_email(c["author"])].id,
                             body=c["body"], is_internal=bool(c.get("internal")),
                             created_at=to_utc(c["at"])))


def add_to_existing(db, folder, it, subject, ticket, assigned, users):
    """El correo es de un ticket que ya vino del sistema anterior: se le agrega lo del correo."""
    created = to_utc(it["received_at"])
    requester = users[normalize_email(it["requester_email"])]
    db.add(TicketComment(ticket_id=ticket.id, user_id=requester.id, is_internal=False, created_at=created,
                         body=f"{it['description'].strip()}\n\nReportó: {it['reported_by']}\n\n{mark(subject)}"))
    if assigned and ticket.assigned_to_user_id is None:
        ticket.assigned_to_user_id = assigned.id
        db.add(TicketHistory(ticket_id=ticket.id, user_id=assigned.id, action="ASSIGN",
                             old_value=None, new_value=str(assigned.id), created_at=created))
    add_attachments_and_comments(db, folder, it, ticket, requester, users)
    print(f"  Agregado al ticket #{ticket.id} (folio {it['folio']}): {subject}")


def run(folder, apply=False):
    with open(os.path.join(folder, "tickets_correos.json"), encoding="utf-8") as f:
        items = json.load(f)

    db = SessionLocal()
    users = {u.email.lower(): u for u in db.query(User).all()}
    locations = {key(loc.name): loc for loc in db.query(Location).all()}
    incidencias = {key(i.name): i for i in db.query(Incidencia).all()}
    subs = {(s.incidencia_id, key(s.name)): s for s in db.query(Subincidencia).all()}

    def find_user(email, required=True):
        if not email:
            return None
        user = users.get(normalize_email(email))
        if user is None and required:
            raise SystemExit(f"No existe el usuario {normalize_email(email)}")
        return user

    plan, errors = [], []
    for n, it in enumerate(items, 1):
        subject = it["subject"].strip()
        already = db.query(Ticket.id).filter(Ticket.description.contains(mark(subject))).first() or \
            db.query(TicketComment.id).filter(TicketComment.body.contains(mark(subject))).first()
        if already:
            print(f"{n}. Ya cargado, se omite: {subject}")
            continue
        if it.get("folio"):
            existing = db.query(Ticket).filter(Ticket.description.contains(f"(folio {it['folio']})")).first()
            assigned = find_user(it.get("assigned_to"), required=False)
            requester_email = normalize_email(it["requester_email"])
            if existing is None:
                errors.append(f"{n}. {subject}: no existe el ticket importado con folio {it['folio']}")
            if it.get("assigned_to") and assigned is None:
                errors.append(f"{n}. {subject}: no existe el técnico {it['assigned_to']}")
            if requester_email not in users:
                errors.append(f"{n}. {subject}: no existe el solicitante {requester_email}")
            for name in it.get("attachments", []):
                if not os.path.isfile(os.path.join(folder, name)):
                    errors.append(f"{n}. {subject}: falta el archivo {name}")
            plan.append((it, subject, existing, None, None, assigned, requester_email))
            print(f"{n}. {it['received_at'][:16].replace('T', ' ')}  se agrega al ticket #{existing.id if existing else '?'}"
                  f" (folio {it['folio']})  |  técnico: {assigned.name if assigned else '-'}  |  "
                  f"adjuntos: {len(it.get('attachments', []))}  |  comentarios: {len(it.get('comments', [])) + 1}")
            continue
        inc = incidencias.get(key(it["incidencia"]))
        sub = subs.get((inc.id, key(it["subincidencia"]))) if inc else None
        location = locations.get(key(it["location"]))
        assigned = find_user(it.get("assigned_to"), required=False) if it.get("assigned_to") else None
        for label, value, ok in (("categoría", it["incidencia"], inc), ("subcategoría", it["subincidencia"], sub),
                                 ("ubicación", it["location"], location)):
            if not ok:
                errors.append(f"{n}. {subject}: no existe la {label} '{value}'")
        if it.get("assigned_to") and assigned is None:
            errors.append(f"{n}. {subject}: no existe el técnico {it['assigned_to']}")
        if it["status"] not in VALID_STATUS:
            errors.append(f"{n}. {subject}: estado no válido '{it['status']}'")
        for name in it.get("attachments", []):
            if not os.path.isfile(os.path.join(folder, name)):
                errors.append(f"{n}. {subject}: falta el archivo {name}")
        for c in it.get("comments", []):
            if normalize_email(c["author"]) not in users:
                errors.append(f"{n}. {subject}: no existe el autor del comentario {c['author']}")
        requester_email = normalize_email(it["requester_email"])
        plan.append((it, subject, inc, sub, location, assigned, requester_email))
        print(f"{n}. {it['received_at'][:16].replace('T', ' ')}  {it['location']}  |  "
              f"{it['incidencia']} / {it['subincidencia']}  |  {it['status']}  |  "
              f"técnico: {assigned.name if assigned else '-'}  |  solicitante: {requester_email}"
              f"{'' if requester_email in users else ' (NUEVO)'}  |  adjuntos: {len(it.get('attachments', []))}")

    if errors:
        print("\nHay errores, no se cargó nada:")
        print("\n".join("  " + e for e in errors))
        db.close()
        sys.exit(1)
    if not apply:
        print("\nNo se cambió nada. Para cargar: agrega --aplicar")
        db.close()
        return

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    for it, subject, inc, sub, location, assigned, requester_email in plan:
        if it.get("folio"):
            add_to_existing(db, folder, it, subject, inc, assigned, users)
            continue
        created = to_utc(it["received_at"])
        requester = users.get(requester_email)
        if requester is None:
            requester = User(name=it.get("reported_by", requester_email.split("@")[0])[:150],
                             email=requester_email, password_hash=hash_password(secrets.token_urlsafe(24)),
                             role="user", location_id=location.id, is_active=True)
            db.add(requester)
            db.flush()
            users[requester_email] = requester

        description = (f"{it['description'].strip()}\n\nReportó: {it['reported_by']}\n\n{mark(subject)}")
        resolved = to_utc(it["resolved_at"]) if it.get("resolved_at") else None
        ticket = Ticket(incidencia_id=inc.id, subincidencia_id=sub.id, created_by_user_id=requester.id,
                        assigned_to_user_id=assigned.id if assigned else None, location_id=location.id,
                        description=description, status=it["status"], priority=it.get("priority", "medium"),
                        created_at=created, updated_at=resolved or created)
        db.add(ticket)
        db.flush()

        history = [TicketHistory(ticket_id=ticket.id, user_id=requester.id, action="CREATE",
                                 old_value=None, new_value="Ticket creado", created_at=created)]
        if assigned:
            history.append(TicketHistory(ticket_id=ticket.id, user_id=assigned.id, action="ASSIGN",
                                         old_value=None, new_value=str(assigned.id), created_at=created))
        if it["status"] in ("in_progress", "pending"):
            history.append(TicketHistory(ticket_id=ticket.id, user_id=assigned.id if assigned else None,
                                         action="STATUS", old_value="open", new_value=it["status"],
                                         created_at=created))
        if it["status"] == "closed":
            when = resolved or created
            history.append(TicketHistory(ticket_id=ticket.id, user_id=assigned.id if assigned else None,
                                         action="STATUS", old_value="in_progress", new_value="resolved",
                                         created_at=when))
            history.append(TicketHistory(ticket_id=ticket.id, user_id=assigned.id if assigned else None,
                                         action="CLOSE", old_value="resolved", new_value="closed",
                                         created_at=when))

        db.add_all(history)
        add_attachments_and_comments(db, folder, it, ticket, requester, users)
        print(f"  Creado ticket #{ticket.id}: {subject}")

    db.commit()
    db.close()
    print("Listo.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], apply="--aplicar" in sys.argv)
