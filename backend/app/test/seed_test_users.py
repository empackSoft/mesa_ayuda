"""
Crea usuarios de prueba (uno por rol) para probar el frontend en LOCAL.
No usar en producción: la contraseña es conocida.

Uso:
    docker compose exec backend python -m test.seed_test_users
"""
from database import SessionLocal
from models.user import User
from security.password import hash_password

# Se importan para que SQLAlchemy resuelva todas las relaciones
import models.ticket  # noqa: F401
import models.ticketHistory  # noqa: F401
import models.ticketAttachment  # noqa: F401
import models.ticketComment  # noqa: F401
import models.incidencia  # noqa: F401
import models.subincidencia  # noqa: F401

TEST_PASSWORD = "Prueba2026"

TEST_USERS = [
    ("Prueba Usuario", "prueba.user@example.com", "user"),
    ("Prueba Soporte", "prueba.soporte@example.com", "support"),
    ("Prueba Admin", "prueba.admin@example.com", "admin"),
]


def run():
    db = SessionLocal()
    try:
        for name, email, role in TEST_USERS:
            if db.query(User).filter(User.email == email).first():
                print(f"Ya existe: {email}")
                continue
            db.add(User(
                name=name,
                email=email,
                role=role,
                password_hash=hash_password(TEST_PASSWORD),
                is_active=True,
            ))
            print(f"Creado: {email} ({role})")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
