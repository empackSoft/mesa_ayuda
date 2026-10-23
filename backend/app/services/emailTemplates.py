from datetime import timedelta
from html import escape
from urllib.parse import urlparse

from services.emailService import FRONTEND_URL

# Plantillas HTML de los correos (diseño de vista-estado.html y vista-restablecer-contrasena.html).
# Las imágenes (cid:logo, cid:firma, cid:mascota) las adjunta emailService.

SUPPORT_PHONE = "55 7665 2900"
SUPPORT_EMAIL = "sistemas@empack.com.mx"
SUPPORT_SITE_LABEL = urlparse(FRONTEND_URL).netloc or "Mesa de Ayuda"

# México ya no tiene horario de verano: siempre UTC-6
MX_OFFSET = timedelta(hours=-6)

MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

STATUS_COLORS = {
    "open": "#F08A00",
    "in_progress": "#7A2FF2",
    "pending": "#64748B",
    "resolved": "#00B2D6",
    "closed": "#1B2A4A",
    "cancelled": "#F0145A",
}

PRIORITY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "urgent": "Urgente",
}

FONT = "font-family:Segoe UI,Arial,sans-serif;"


def _text(value) -> str:
    """Escapa el texto y respeta los saltos de línea."""
    return escape(str(value or "")).replace("\n", "<br>")


def format_date(value) -> str:
    if value is None:
        return "—"
    local = value + MX_OFFSET
    return f"{local.day} {MONTHS[local.month - 1]} {local.year}, {local:%H:%M} h"


def _button(link: str, label: str, margin: str) -> str:
    return f"""
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:{margin};">
          <tr>
            <td style="background-color:#1B2A4A;border-radius:8px;">
              <a href="{escape(link)}" style="display:inline-block;padding:12px 26px;{FONT}font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none;">
                {label}
              </a>
            </td>
          </tr>
        </table>"""


def _note_box(html: str) -> str:
    return f"""
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">
          <tr>
            <td style="background-color:#F5F5F7;border-radius:12px;padding:16px 22px;{FONT}font-size:13px;line-height:20px;color:#4A5568;">
              {html}
            </td>
          </tr>
        </table>"""


def _layout(title: str, preheader: str, header_right: str, body: str, legal: str) -> str:
    site = escape(FRONTEND_URL or "#")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<!--[if mso]><style>table,td,div,p,a{{font-family:Arial,sans-serif !important;}}</style><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#F2F4F7;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;color:#F2F4F7;">
{escape(preheader)}
</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F2F4F7;">
<tr><td align="center" style="padding:32px 16px;">

  <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background-color:#FFFFFF;border:1px solid #E3E6EB;">

    <!-- Encabezado -->
    <tr>
      <td style="padding:24px 40px 20px 40px;border-bottom:2px solid #C8102E;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td valign="middle">
              <img src="cid:logo" width="140" alt="EM-PACK Cajas de Cartón" style="display:block;border:0;outline:none;width:140px;height:auto;">
            </td>
            <td valign="middle" align="right" style="{FONT}">
              <p style="margin:0;font-size:13px;font-weight:600;color:#1B2A4A;">Mesa de Ayuda</p>
              {header_right}
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- Cuerpo -->
    <tr>
      <td style="padding:32px 40px 8px 40px;{FONT}">
{body}
      </td>
    </tr>

    <!-- Firma -->
    <tr>
      <td style="padding:24px 40px 28px 40px;border-top:2px solid #C8102E;{FONT}">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td width="76" valign="middle" style="padding-right:16px;">
              <img src="cid:firma" width="60" alt="EM PACK Sistemas" style="display:block;border:0;width:60px;height:auto;">
            </td>
            <td valign="middle" style="border-left:1px solid #EDEFF2;padding-left:16px;{FONT}">
              <p style="margin:0;font-size:14px;font-weight:600;color:#1B2A4A;">Departamento de Sistemas</p>
              <p style="margin:2px 0 8px 0;font-size:13px;color:#4A5568;">EMPACK de México, S.A. de C.V.</p>
              <p style="margin:0;font-size:12px;line-height:20px;color:#8A93A3;">
                Tel. {SUPPORT_PHONE}<br>
                <a href="mailto:{SUPPORT_EMAIL}" style="color:#8A93A3;text-decoration:none;">{SUPPORT_EMAIL}</a> &nbsp;·&nbsp;
                <a href="{site}" style="color:#C8102E;text-decoration:none;">{escape(SUPPORT_SITE_LABEL)}</a>
              </p>
            </td>
            <td width="60" valign="bottom" align="right">
              <img src="cid:mascota" width="56" alt="" style="display:block;border:0;width:56px;height:auto;">
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- Aviso legal -->
    <tr>
      <td style="padding:16px 40px 20px 40px;background-color:#F7F8FA;{FONT}font-size:10px;line-height:15px;color:#A0A7B4;">
        {legal}
        Consulta nuestro
        <a href="https://www.empack.com.mx" style="color:#A0A7B4;text-decoration:underline;">Aviso de Privacidad</a>.
        Correo generado automáticamente por la Mesa de Ayuda.
      </td>
    </tr>

  </table>

</td></tr>
</table>
</body>
</html>"""


def _detail_row(label: str, value: str, first: bool = False) -> str:
    width = ' width="38%"' if first else ""
    return f"""
          <tr>
            <td{width} style="padding:11px 0;border-bottom:1px solid #EDEFF2;font-size:13px;color:#8A93A3;">{label}</td>
            <td style="padding:11px 0;border-bottom:1px solid #EDEFF2;font-size:13px;color:#1B2A4A;">{value}</td>
          </tr>"""


# Fragmento de la conversación en el correo de un comentario
PREVIOUS_MAX_CHARS = 500


def _initials(name: str) -> str:
    return "".join(word[0].upper() for word in (name or "").split()[:2]) or "?"


def _message_block(m: dict) -> str:
    """
    Un mensaje como en la conversación del sistema: avatar con iniciales,
    nombre · rol · fecha y el texto en una burbuja.
    m: author, role, created_at, body, is_new, is_internal
    """
    body = m["body"] or ""
    if not m["is_new"] and len(body) > PREVIOUS_MAX_CHARS:
        body = body[:PREVIOUS_MAX_CHARS].rstrip() + "…"

    # Mismos colores que los avatares del sistema: dorado el usuario, azul Soporte
    avatar = "#BC9451" if m.get("role") in ("Solicitante", "Usuario") else "#0B2879"
    bubble = "#FFF4E0" if m["is_internal"] else "#FFFFFF"
    text_color = "#1D1D1F" if m["is_new"] else "#6E6E73"

    role = f" &nbsp;{_text(m['role'])}" if m.get("role") else ""
    internal = " · Nota interna" if m["is_internal"] else ""
    badge = (
        '&nbsp; <span style="background-color:#C8102E;border-radius:10px;padding:1px 8px;'
        'font-size:10px;font-weight:700;color:#FFFFFF;">Nuevo</span>'
        if m["is_new"] else ""
    )

    return f"""
          <tr>
            <td style="padding:0 0 14px 0;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td width="34" valign="top">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td width="34" height="34" align="center" valign="middle" style="width:34px;height:34px;border-radius:17px;background-color:{avatar};{FONT}font-size:12px;font-weight:600;line-height:34px;color:#FFFFFF;">
                          {_text(_initials(m["author"]))}
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td valign="top" style="padding-left:12px;{FONT}">
                    <p style="margin:0 0 6px 0;font-size:12px;line-height:18px;color:#8A93A3;">
                      <strong style="font-size:13px;color:#1D1D1F;">{_text(m["author"])}</strong>{role}{internal}
                      &nbsp;·&nbsp;{format_date(m["created_at"])}{badge}
                    </p>
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background-color:{bubble};border-radius:16px;padding:10px 14px;{FONT}font-size:14px;line-height:21px;color:{text_color};">
                          {_text(body)}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>"""


def render_conversation(conversation: dict) -> str:
    """
    conversation: {"older": bool, "messages": [...]}.
    Solo va el mensaje anterior y el nuevo, dentro de una tarjeta tipo vista previa;
    "older" indica que hay mensajes más viejos sin mostrar (⋯ arriba).
    """
    older = f"""
          <tr>
            <td align="center" style="padding:0 0 12px 0;{FONT}font-size:20px;line-height:10px;letter-spacing:2px;color:#B4B9C3;">&middot;&middot;&middot;</td>
          </tr>""" if conversation.get("older") else ""

    return f"""
        <!-- Conversación (vista previa) -->
        <p style="margin:0 0 10px 0;font-size:12px;font-weight:600;color:#86868B;">Conversación</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="background-color:#F2F3F5;border-radius:20px;padding:18px 18px 4px 18px;box-shadow:0 6px 24px rgba(16,24,40,0.08);">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
{older}{"".join(_message_block(m) for m in conversation["messages"])}
              </table>
            </td>
          </tr>
        </table>"""


def render_ticket_email(
        ticket,
        title: str,
        message: str,
        status_label: str,
        link: str,
        greeting_name: str = None,
        footer: str = None,
        is_new: bool = False,
        conversation: dict = None
) -> str:
    """
    is_new: correo de ticket recién creado (lleva fecha, solicitante y descripción).
    Los avisos sobre un ticket existente solo dicen qué pasó; el detalle está en el sistema.
    conversation: correo de un comentario; en vez del detalle va un fragmento de la conversación
    (ver render_conversation).
    El número de ticket no se repite en el detalle: ya va en el encabezado.
    """
    number = f"#{ticket.id}"
    creator = ticket.created_by
    category = " · ".join(
        item.name for item in (ticket.incidencia, ticket.subincidencia) if item
    ) or "—"

    # A la derecha del estado: quién atiende el ticket
    if ticket.assigned_to:
        attended = (
            f'Atendido por <strong style="color:#1B2A4A;">{_text(ticket.assigned_to.name)}</strong>'
        )
    else:
        attended = "Sin asignar"

    rows = []
    if is_new:
        rows += [
            ("Fecha de registro", format_date(ticket.created_at)),
            ("Solicitante", _text(creator.name if creator else "—")),
        ]
    rows += [
        ("Ubicación", _text(ticket.location.name if ticket.location else "—")),
        ("Categoría", _text(category)),
        ("Prioridad", PRIORITY_LABELS.get(ticket.priority, _text(ticket.priority))),
    ]
    rows_html = "".join(
        _detail_row(label, value, first=i == 0) for i, (label, value) in enumerate(rows)
    )
    if conversation:
        details = render_conversation(conversation)
    else:
        details = f"""
        <!-- Detalle -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid #EDEFF2;">
{rows_html}
        </table>"""

    description = f"""
        <!-- Descripción -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:28px;">
          <tr>
            <td style="background-color:#F5F5F7;border-radius:12px;padding:18px 22px;{FONT}">
              <p style="margin:0 0 6px 0;font-size:12px;font-weight:600;color:#86868B;">Descripción</p>
              <p style="margin:0;font-size:15px;line-height:23px;color:#1D1D1F;">{_text(ticket.description)}</p>
            </td>
          </tr>
        </table>""" if is_new else ""

    greeting = f"Hola {_text(greeting_name.split()[0])}, " if greeting_name else ""

    body = f"""
        <!-- Estado y quién lo atiende -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td valign="middle">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="background-color:{STATUS_COLORS.get(ticket.status, '#64748B')};border-radius:8px;padding:7px 16px;{FONT}font-size:13px;font-weight:700;line-height:16px;color:#FFFFFF;">
                    {_text(status_label)}
                  </td>
                </tr>
              </table>
            </td>
            <td valign="middle" align="right" style="{FONT}font-size:13px;color:#8A93A3;">
              {attended}
            </td>
          </tr>
        </table>

        <h1 style="margin:18px 0 8px 0;font-size:22px;line-height:30px;font-weight:600;color:#1B2A4A;">
          {_text(title)}
        </h1>
        <p style="margin:0 0 28px 0;font-size:14px;line-height:22px;color:#4A5568;">
          {greeting}{_text(message)}
        </p>

{details}
{description}
{_note_box(_text(footer)) if footer else ""}
{_button(link, "Consultar ticket", "30px 0 8px 0")}

        <p style="margin:18px 0 32px 0;font-size:12px;line-height:19px;color:#8A93A3;">
          Para agregar información, entra al ticket y escribe un comentario.
        </p>"""

    return _layout(
        title=f"Ticket {number} · Mesa de Ayuda",
        preheader=f"Ticket {number}: {title}",
        header_right=(
            f'<p style="margin:2px 0 0 0;font-size:12px;color:#8A93A3;">'
            f'Ticket <strong style="color:#1B2A4A;">{number}</strong></p>'
        ),
        body=body,
        legal=(
            "Este mensaje y sus adjuntos son confidenciales y para uso exclusivo del destinatario. "
            "Si lo recibiste por error, notifícalo al remitente y elimínalo."
        )
    )


def render_password_reset_email(name: str, link: str, minutes: int) -> str:
    safe_link = escape(link)
    body = f"""
        <h1 style="margin:0 0 8px 0;font-size:22px;line-height:30px;font-weight:600;color:#1B2A4A;">
          Restablece tu contraseña
        </h1>
        <p style="margin:0 0 24px 0;font-size:14px;line-height:22px;color:#4A5568;">
          Hola {_text(name.split()[0] if name else "")}, recibimos una solicitud para cambiar la contraseña de tu cuenta en la Mesa de Ayuda.
          Da clic en el botón para crear una nueva.
        </p>
{_button(link, "Crear nueva contraseña", "0 0 16px 0")}

        <p style="margin:0 0 4px 0;font-size:13px;color:#4A5568;">
          El enlace es válido durante <strong style="color:#1B2A4A;">{minutes} minutos</strong> y solo puede usarse una vez.
        </p>
{_note_box(
        '<strong style="color:#1B2A4A;">¿No lo solicitaste?</strong> Ignora este correo; '
        'tu contraseña actual seguirá funcionando. Si recibes estos avisos con frecuencia, repórtalo a Sistemas.'
    )}

        <p style="margin:24px 0 32px 0;font-size:11px;line-height:17px;color:#A0A7B4;word-break:break-all;">
          Si el botón no funciona, copia esta dirección en tu navegador:<br>
          <a href="{safe_link}" style="color:#8A93A3;">{safe_link}</a>
        </p>"""

    return _layout(
        title="Restablecer contraseña · Mesa de Ayuda",
        preheader=f"Usa este enlace para crear una nueva contraseña. Vence en {minutes} minutos.",
        header_right="",
        body=body,
        legal=(
            "Por seguridad, el personal de Sistemas nunca te pedirá tu contraseña por correo o teléfono. "
            "Este mensaje es confidencial y para uso exclusivo del destinatario."
        )
    )
