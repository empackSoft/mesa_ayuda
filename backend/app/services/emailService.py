import smtplib
import ssl
import os
from email.message import EmailMessage
from email.header import Header


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

FRONTEND_URL = os.getenv("FRONTEND_URL", "")
NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"


def send_email(to: str, subject: str, body: str):
    """
    Envía un correo best-effort.
    Si algo falla, lo registra y NO lanza excepción,
    para no interrumpir la operación principal.
    """
    if not NOTIFICATIONS_ENABLED:
        print("[EMAIL] Notificaciones desactivadas, no se envía correo")
        return

    if not to:
        print("[EMAIL] Sin destinatario, se omite el envío")
        return

    if not SMTP_HOST or not SMTP_USER:
        print("[EMAIL] SMTP no configurado, se omite el envío")
        return

    try:
        message = EmailMessage()
        message["From"] = SMTP_FROM
        message["To"] = to
        message["Subject"] = Header(subject, "utf-8").encode()
        message.set_content(body, charset="utf-8")

        raw_message = message.as_bytes()

        if SMTP_USE_TLS:
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [to], raw_message)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [to], raw_message)

        print(f"[EMAIL] Enviado a {to}: {subject}")

    except Exception as e:
        # Best-effort: registrar y continuar
        print(f"[EMAIL] Error al enviar a {to}: {e}")


def build_ticket_link(ticket_id: int) -> str:
    return f"{FRONTEND_URL}/tickets/{ticket_id}"