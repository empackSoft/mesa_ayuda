"""
Asigna contraseña a un usuario existente o crea un admin nuevo.
Sirve para el primer acceso en el VPS y para usuarios importados
(el importador les pone una contraseña aleatoria).

La contraseña se pide en pantalla (no queda en el historial de la terminal).

Uso:
    docker compose exec -it backend python scripts/set_password.py correo@empack.com.mx
    docker compose exec -it backend python scripts/set_password.py correo@empack.com.mx --admin "Nombre Apellido"
"""
import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func  # noqa: E402

from database import SessionLocal  # noqa: E402
from models.user import User  # noqa: E402
from security.password import hash_password  # noqa: E402

# Se importan para que SQLAlchemy resuelva todas las relaciones
import models.location  # noqa: E402,F401
import models.ticket  # noqa: E402,F401
import models.ticketHistory  # noqa: E402,F401
import models.ticketAttachment  # noqa: E402,F401
import models.ticketComment  # noqa: E402,F401
import models.incidencia  # noqa: E402,F401
import models.subincidencia  # noqa: E402,F401

MIN_LENGTH = 8


def ask_password():
    while True:
        password = getpass.getpass("Nueva contraseña: ")
        if len(password) < MIN_LENGTH:
            print(f"Debe tener al menos {MIN_LENGTH} caracteres.")
            continue
        if getpass.getpass("Repítela: ") != password:
            print("No coinciden, intenta de nuevo.")
            continue
        return password


def run():
    parser = argparse.ArgumentParser(description="Asigna contraseña o crea un admin")
    parser.add_argument("email")
    parser.add_argument("--admin", metavar="NOMBRE",
                        help="Crea el usuario como admin si no existe")
    args = parser.parse_args()
    email = args.email.strip().lower()

    db = SessionLocal()
    try:
        user = db.query(User).filter(func.lower(User.email) == email).first()
        if user is None and not args.admin:
            print(f"No existe {email}. Para crearlo como admin agrega --admin \"Nombre\".")
            sys.exit(1)

        password = ask_password()

        if user is None:
            user = User(name=args.admin, email=email, role="admin",
                        password_hash=hash_password(password), is_active=True)
            db.add(user)
            print(f"Admin creado: {email}")
        else:
            user.password_hash = hash_password(password)
            user.is_active = True
            print(f"Contraseña actualizada: {email} (rol {user.role})")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
