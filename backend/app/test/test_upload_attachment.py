import io
from fastapi import UploadFile, HTTPException

from database import SessionLocal
from services.ticketService import upload_attachment, MAX_FILE_SIZE

import sys
import os

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

def make_file(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def run():
    db = SessionLocal()

    # AJUSTA este id a un ticket real, abierto y asignado
    TICKET_ID = 1

    print("== 1. Archivo válido ==")
    try:
        f = make_file("evidencia.png", b"fake-png-bytes")
        result = upload_attachment(db, TICKET_ID, f)
        print("OK ->", result["attachment_path"])
    except HTTPException as e:
        print("FALLO:", e.status_code, e.detail)

    print("== 2. Extensión no permitida ==")
    try:
        f = make_file("virus.exe", b"data")
        upload_attachment(db, TICKET_ID, f)
        print("FALLO: debió rechazar")
    except HTTPException as e:
        print("OK ->", e.status_code, e.detail)

    print("== 3. Archivo vacío ==")
    try:
        f = make_file("vacio.png", b"")
        upload_attachment(db, TICKET_ID, f)
        print("FALLO: debió rechazar")
    except HTTPException as e:
        print("OK ->", e.status_code, e.detail)

    print("== 4. Archivo demasiado grande ==")
    try:
        big = b"x" * (MAX_FILE_SIZE + 1)
        f = make_file("grande.pdf", big)
        upload_attachment(db, TICKET_ID, f)
        print("FALLO: debió rechazar")
    except HTTPException as e:
        print("OK ->", e.status_code, e.detail)

    print("== 5. Ticket inexistente ==")
    try:
        f = make_file("evidencia.png", b"data")
        upload_attachment(db, 999999, f)
        print("FALLO: debió rechazar")
    except HTTPException as e:
        print("OK ->", e.status_code, e.detail)

    db.close()


if __name__ == "__main__":
    run()