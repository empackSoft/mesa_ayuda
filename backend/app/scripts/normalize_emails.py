"""
Deja todos los correos de usuarios en @empack.com.mx.

Sirve para una base que ya existe (por ejemplo, una importada sin --real-emails, con
correos @importado.example.com, o con dominios mal escritos como empakatodo.com.mx).
Se conserva la parte antes de la @ y se cambia el dominio. Los técnicos importados
recuperan su correo real (sistemas@, sistemas2@...) según la lista STAFF del importador.

Si el correo corregido ya lo tiene otro usuario, se fusionan: tickets, comentarios,
historial, adjuntos, encuestas y avisos pasan al usuario que ya existía y el duplicado
se borra.

No toca los usuarios de prueba (@example.com).

Uso (dentro del contenedor backend):
    python scripts/normalize_emails.py            # solo muestra qué cambiaría
    python scripts/normalize_emails.py --aplicar  # hace los cambios
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

from database import SessionLocal  # noqa: E402
from scripts.import_legacy import COMPANY_DOMAIN, STAFF, key, normalize_email  # noqa: E402

TEST_SUFFIX = "@example.com"

# (tabla, columna) que apuntan a users.id
USER_REFERENCES = [
    ("tickets", "created_by_user_id"),
    ("tickets", "assigned_to_user_id"),
    ("ticket_comments", "user_id"),
    ("ticket_history", "user_id"),
    ("ticket_attachments", "uploaded_by"),
    ("ticket_surveys", "user_id"),
    ("notifications", "user_id"),
    ("password_reset_tokens", "user_id"),
]

STAFF_EMAIL_BY_NAME = {key(name): email for name, email, _active in STAFF.values() if email}


def target_email(user):
    email = (user.email or "").strip().lower()
    if email.endswith("@" + COMPANY_DOMAIN):
        return email
    if user.role in ("support", "admin") and key(user.name) in STAFF_EMAIL_BY_NAME:
        return STAFF_EMAIL_BY_NAME[key(user.name)]
    return normalize_email(email)


def merge(db, duplicate_id, keep_id):
    for table, column in USER_REFERENCES:
        db.execute(text(f"UPDATE {table} SET {column} = :keep WHERE {column} = :dup"),
                   {"keep": keep_id, "dup": duplicate_id})
    # En la asignación el historial guarda el id del técnico como texto
    for column in ("old_value", "new_value"):
        db.execute(text(f"UPDATE ticket_history SET {column} = :keep "
                        f"WHERE action = 'ASSIGN' AND {column} = :dup"),
                   {"keep": str(keep_id), "dup": str(duplicate_id)})
    db.execute(text("DELETE FROM users WHERE id = :dup"), {"dup": duplicate_id})


def run(apply=False):
    db = SessionLocal()
    users = db.execute(text("SELECT id, name, email, role, is_active FROM users ORDER BY id")).all()
    by_email = {u.email.lower(): u for u in users}

    changes, merges, skipped = [], [], []
    for u in users:
        email = u.email.lower()
        if email.endswith(TEST_SUFFIX):
            continue
        new = target_email(u)
        if not new:
            skipped.append(u)
            continue
        if new == email:
            continue
        owner = by_email.get(new)
        if owner is not None and owner.id != u.id:
            merges.append((u, owner))
        else:
            changes.append((u, new))
            by_email.pop(email, None)
            by_email[new] = u

    print(f"Correos a corregir: {len(changes)}")
    for u, new in changes:
        print(f"  #{u.id:<4} {u.email:<45} -> {new:<40} {u.name}")
    print(f"Usuarios duplicados a fusionar: {len(merges)}")
    for dup, keep in merges:
        print(f"  #{dup.id:<4} {dup.email:<45} -> #{keep.id} {keep.email} ({keep.name})")
    if skipped:
        print(f"Sin correo que se pueda corregir (se dejan igual): {len(skipped)}")
        for u in skipped:
            print(f"  #{u.id:<4} {u.email}  {u.name}")

    if not apply:
        print("\nNo se cambió nada. Para aplicar: python scripts/normalize_emails.py --aplicar")
        db.close()
        return

    for dup, keep in merges:
        merge(db, dup.id, keep.id)
    for u, new in changes:
        db.execute(text("UPDATE users SET email = :email WHERE id = :id"), {"email": new, "id": u.id})
    db.commit()
    db.close()
    print("\nListo.")


if __name__ == "__main__":
    run(apply="--aplicar" in sys.argv)
