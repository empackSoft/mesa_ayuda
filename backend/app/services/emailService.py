import smtplib
import ssl
import os
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

FRONTEND_URL = os.getenv("FRONTEND_URL", "")
NOTIFICATIONS_ENABLED = os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true"

# Modo prueba: si tiene un correo, TODOS los avisos van solo ahí (sin importar el rol).
# Vacío = producción: cada aviso va a sus destinatarios reales.
EMAIL_TEST_RECIPIENT = os.getenv("EMAIL_TEST_RECIPIENT", "").strip()

# Direcciones que nunca existen (usuarios de prueba e importados sin correo real)
FAKE_EMAIL_SUFFIX = "example.com"

# Los correos se mandan en segundo plano: un SMTP lento no debe frenar la respuesta
# (con varios destinatarios, crear un ticket llegaba a tardar más de un minuto)
_email_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="email")


def _clean(emails, exclude=()) -> list:
    """Quita vacíos, falsos y repetidos, respetando el orden."""
    if isinstance(emails, str):
        emails = [emails]
    seen = {e.strip().lower() for e in exclude if e}
    result = []
    for email in emails or []:
        email = (email or "").strip().lower()
        if not email or email in seen or email.endswith(FAKE_EMAIL_SUFFIX):
            continue
        seen.add(email)
        result.append(email)
    return result


def send_email(to, subject: str, body: str, cc=None):
    """
    Encola UN correo best-effort (Para + CC) y regresa de inmediato.
    Si algo falla, lo registra y NO lanza excepción,
    para no interrumpir la operación principal.
    """
    if not NOTIFICATIONS_ENABLED:
        print("[EMAIL] Notificaciones desactivadas, no se envía correo")
        return

    to = _clean(to)
    cc = _clean(cc, exclude=to)
    if not to and cc:
        to, cc = cc[:1], cc[1:]

    if not to:
        print("[EMAIL] Sin destinatario, se omite el envío")
        return

    if not SMTP_HOST or not SMTP_USER:
        print("[EMAIL] SMTP no configurado, se omite el envío")
        return

    if EMAIL_TEST_RECIPIENT:
        body = (
            "(Modo prueba: en producción este correo iría a)\n"
            f"Para: {', '.join(to)}\n"
            f"CC: {', '.join(cc) or '—'}\n\n"
            f"{body}"
        )
        print(f"[EMAIL] Modo prueba. En producción iría a Para: {to} CC: {cc}")
        subject = f"[PRUEBA] {subject}"
        to, cc = [EMAIL_TEST_RECIPIENT], []

    _email_executor.submit(_deliver, to, cc, subject, body)


def _deliver(to: list, cc: list, subject: str, body: str):
    recipients = ", ".join(to + cc)
    try:
        message = EmailMessage()
        message["From"] = SMTP_FROM
        message["To"] = ", ".join(to)
        if cc:
            message["Cc"] = ", ".join(cc)
        message["Subject"] = subject  # EmailMessage codifica UTF-8 y pliega asuntos largos
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain=SMTP_FROM.split("@")[-1])
        message.set_content(body, charset="utf-8")

        raw_message = message.as_bytes()

        if SMTP_USE_TLS:
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, to + cc, raw_message)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, to + cc, raw_message)

        print(f"[EMAIL] Enviado a {recipients}: {subject}")

    except Exception as e:
        print(f"[EMAIL] Error al enviar a {recipients}: {e}")


def build_ticket_link(ticket_id: int) -> str:
    return f"{FRONTEND_URL}/tickets/{ticket_id}"
