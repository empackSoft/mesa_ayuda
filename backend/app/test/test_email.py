"""
Prueba aislada de envío SMTP, con la misma configuración que emailService.

A diferencia de send_email (best-effort), aquí los errores SÍ se muestran
completos y se imprime el diálogo SMTP, para diagnosticar entregas.

Uso (dentro del contenedor, toma las variables del .env):
    docker compose exec backend python -m test.test_email correo1@gmail.com [correo2 ...]
"""
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from email.header import Header
from email.utils import formatdate, make_msgid

from services.emailService import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_USE_TLS,
)


def build_message(to: str) -> bytes:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to
    message["Subject"] = Header(f"Prueba Mesa de Ayuda - {now}", "utf-8").encode()
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=SMTP_FROM.split("@")[-1])
    message.set_content(
        f"Correo de prueba de la Mesa de Ayuda EmPack.\n"
        f"Enviado: {now}\n"
        f"Servidor: {SMTP_HOST}:{SMTP_PORT}\n"
        f"Acentos y ñ: canción, año, información.\n",
        charset="utf-8",
    )
    return message.as_bytes()


def run(recipients: list[str]):
    print(f"SMTP_HOST={SMTP_HOST} SMTP_PORT={SMTP_PORT} TLS={SMTP_USE_TLS}")
    print(f"SMTP_USER={SMTP_USER} SMTP_FROM={SMTP_FROM}")
    print(f"SMTP_PASSWORD={'(definida)' if SMTP_PASSWORD else '(VACÍA / None)'}")

    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        sys.exit("Faltan variables SMTP en el .env (¿se recargó con 'docker compose up -d backend'?)")

    context = ssl.create_default_context()
    if SMTP_USE_TLS:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
    else:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15)

    with server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("[OK] Login correcto")
        # Depuración después del login: así no se imprime la contraseña (AUTH en base64)
        server.set_debuglevel(1)
        for to in recipients:
            refused = server.sendmail(SMTP_FROM, [to], build_message(to))
            if refused:
                print(f"\n[RECHAZADO] {to}: {refused}")
            else:
                print(f"\n[OK] Aceptado por el servidor para {to}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python -m test.test_email correo1@dominio.com [correo2 ...]")
    run(sys.argv[1:])
