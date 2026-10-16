"""
Importa los datos del sistema de tickets anterior (dump de MySQL/MariaDB "empacksopo_ticket").

Uso (dentro del contenedor backend):
    python scripts/import_legacy.py /tmp/respaldo.sql            # importa
    python scripts/import_legacy.py /tmp/respaldo.sql --replace  # borra lo importado antes y vuelve a importar
    python scripts/import_legacy.py /tmp/respaldo.sql --real-emails

Por defecto los correos se cambian a @importado.example.com para que, al probar en local,
ningún aviso llegue a personas reales. En producción usar --real-emails.

Qué se toma del sistema anterior:
- ubicaciones / ubicación del ticket   -> locations (ubicaciones)
- correo + nombre de quien levantó      -> users (rol user, contraseña aleatoria: no pueden entrar
                                            hasta que un admin les asigne una)
- asesor                                -> users (rol support)
- asunto / tipo_incidencia              -> incidencias / subincidencias
- ticket                                -> tickets (+ historial: creado, asignado, resuelto, cerrado)
- chat                                  -> ticket_comments
- solucion                              -> comentario final del técnico

Notas sobre los datos de origen:
- Fechas en 3 formatos: "MM/DD/YYYY" (2020-2022, sin hora: se usa 12:00),
  "DD-MM-YY HH:MM:SS" y vacías (se toma el primer mensaje del chat o la fecha de respuesta).
- Desde el ticket 3312 (15/nov/2024, cambio de servidor) la hora de creación está en UTC;
  antes, en hora de México. "respuesta" siempre está en hora de México.
- En el chat, desde ese cambio la fecha viene con día y año invertidos (2014-10-26 = 14/oct/2026).
- El sistema anterior no tenía prioridad: se usa "medium", o "high"/"urgent" si el mensaje dice urgente.
- No se importan contraseñas (eran MD5) ni archivos adjuntos (no vienen en el dump).
"""
import io
import os
import re
import secrets
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta

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

IMPORT_MARK = "— Importado del sistema anterior"
FAKE_DOMAIN = "importado.example.com"
UTC_FROM_TICKET_ID = 3312
MX_OFFSET = timedelta(hours=6)  # hora de México (UTC-6) -> UTC

# Columnas de la tabla `ticket` del sistema anterior
T_ID, T_FECHA, T_SERIE, T_ESTADO, T_NOMBRE, T_EMAIL, T_DEPTO, T_UBIC, T_FRANQ, T_ASUNTO, T_TIPO, \
    T_MENSAJE, T_SOLUCION, T_ASESOR, T_RESPUESTA, T_ARCHIVO = range(16)

STATUS_MAP = {
    "Resuelto": "closed",
    "Pendiente": "pending",
    "En proceso": "in_progress",
    "Cotizando": "pending",
}

# Técnicos del sistema anterior: variantes del campo "asesor" -> (nombre, correo, activo)
STAFF = {
    "hugo": ("Hugo Morgado", "sistemas@empack.com.mx", True),
    "raul": ("Raúl Jaramillo", "raul_jaramillo@empack.com.mx", False),
    "ranulfo": ("Ranulfo Arroyo Delgado", None, False),
    "diego": ("Diego Fernández", "sistemas3@empack.com.mx", True),
    "rene": ("René Martínez", "sistemas5@empack.com.mx", True),
    "fernando": ("Fernando Perdomo De la Cruz", "sistemas2@empack.com.mx", False),
    "armando": ("Armando Hernández", "sistemas6@empack.com.mx", True),
}
# Se busca la primera de estas claves dentro del texto (hay registros como "LSCA.HMH; RAD"
# o "RAUL JARAMILLO RODIGUEZ"): el ticket se asigna al primero que aparece.
ASESOR_KEYS = [
    ("hugo", "hugo"), ("hmh", "hugo"), ("hmm", "hugo"),
    ("jaramillo", "raul"), ("raul", "raul"), ("rjr", "raul"),
    ("ranulfo", "ranulfo"), ("rad", "ranulfo"),
    ("perdomo", "fernando"), ("fpc", "fernando"),
    ("dfi", "diego"), ("diego", "diego"),
    ("rmm", "rene"),
    ("aha", "armando"), ("ahernandez", "armando"),
]

# Ubicaciones escritas distinto en el sistema anterior -> nombre oficial (None = no es ubicación)
LOCATION_ALIASES = {
    "ni": "Niños Héroes I",
    "ninosheroes": "Niños Héroes I",
    "divisi": "División Del Norte",
    "corporaci": "Corporativo Perisur",
    "corporacinperisur": "Corporativo Perisur",
    "sanisidri": "San Isidro",
    "queretatotecnologico": "Querétaro Tecnológico",
    "queretatot": "Querétaro Tecnológico",
    "santateresa": "Plaza Santa Teresa",
    "izcalli": "Tienda Cuautitlán Izcalli",
    "gustavobaz": "Tienda Gustavo Baz",
    "ggallo": "González Gallo",
    "tesorer": None,
}


def location_type(name):
    """Tipo de ubicación por su nombre (mismo criterio que la migración en main.py)."""
    lowered = name.lower()
    if lowered.startswith("cedis"):
        return "cedis"
    if lowered.startswith("corporativo"):
        return "corporate"
    return "branch"


# asunto (normalizado) -> (incidencia, subcategoría por defecto)
CATEGORY_RULES = [
    (("office 365", "offie 365"), "Office 365", None),
    (("erp kepler", "kepler"), "ERP", "Kepler"),
    (("erp drall",), "ERP", "Drall"),
    (("hardware",), "Hardware", None),
    (("software",), "Software", None),
    (("aspel",), "Software", "Aspel"),
    (("telefon",), "Telefonía", None),
    (("biom",), "Biométrico", None),
    (("red",), "Redes", None),
    (("desarrollos nuevo",), "Desarrollos Nuevos", None),
    (("entrega de equipos nuevos",), "Equipo de Cómputo", "Entrega de equipo nuevo"),
    (("pagina web", "página web", "p"), "Página Web", None),
]


# ---------------------------------------------------------------- lectura del dump

def parse_values(text):
    rows, row, i, n = [], None, 0, len(text)
    while i < n:
        c = text[i]
        if row is None:
            if c == '(':
                row = []
            i += 1
            continue
        if c == "'":
            i += 1
            buf = []
            while i < n:
                ch = text[i]
                if ch == '\\':
                    nxt = text[i + 1]
                    buf.append({'n': '\n', 'r': '\r', 't': '\t', '0': ''}.get(nxt, nxt))
                    i += 2
                    continue
                if ch == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        buf.append("'")
                        i += 2
                        continue
                    break
                buf.append(ch)
                i += 1
            row.append(''.join(buf))
            i += 1
            continue
        if c in ',)':
            i += 1
            if c == ')':
                rows.append(row)
                row = None
            continue
        if c.isspace():
            i += 1
            continue
        m = re.match(r"[^,)]+", text[i:i + 50])
        tok = m.group(0).strip()
        row.append(None if tok == 'NULL' else (int(tok) if re.fullmatch(r'-?\d+', tok) else tok))
        i += len(m.group(0))
    return rows


def load_dump(path):
    data = {}
    with io.open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith('INSERT INTO `'):
                table = line[13:line.index('`', 13)]
                values = line[line.index(' VALUES ') + 8:].rstrip().rstrip(';')
                data.setdefault(table, []).extend(parse_values(values))
    return data


# ---------------------------------------------------------------- limpieza de texto

def clean(value):
    value = (value or '').strip()
    if 'Ã' in value:
        try:
            value = value.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return re.sub(r'\s+', ' ', value)


def key(value):
    """Clave para comparar: sin acentos, minúsculas, solo letras y números."""
    value = unicodedata.normalize('NFKD', clean(value)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', value.lower())


def fix_truncated(values):
    """
    En registros viejos el texto se cortó en el primer acento ("Correci" en vez de "Corrección").
    Devuelve {valor_cortado: valor_completo} usando el valor completo más común.
    """
    counts = Counter(values)
    fixes = {}
    for v in counts:
        if not v:
            continue
        candidates = [w for w in counts if len(w) > len(v) and w.startswith(v) and not w[len(v)].isascii()]
        if candidates:
            fixes[v] = max(candidates, key=lambda w: counts[w])
    return fixes


def title_name(value):
    value = clean(value)
    return value.title() if value.isupper() or value.islower() else value


# ---------------------------------------------------------------- fechas

def parse_local(value, date_only_hour=12):
    """Fecha del sistema anterior -> datetime (sin zona). None si no se reconoce."""
    value = (value or '').strip()
    for fmt in ('%d-%m-%y %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    try:
        return datetime.strptime(value, '%m/%d/%Y').replace(hour=date_only_hour)
    except ValueError:
        return None


def parse_chat_date(value, reference):
    """
    El chat guarda 'YYYY-MM-DD HH:MM:SS', pero desde el cambio de servidor
    viene como '20DD-MM-YY'. Se elige la interpretación más cercana al ticket.
    """
    try:
        normal = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None
    options = [normal]
    try:
        options.append(normal.replace(year=2000 + int(value[8:10]), day=int(value[2:4])))
    except ValueError:
        pass
    if reference is None:
        return min(options, key=lambda d: abs(d.year - 2023))
    return min(options, key=lambda d: abs((d - reference).total_seconds()))


# ---------------------------------------------------------------- importación

def delete_imported(db):
    ids = [t.id for t in db.query(Ticket.id).filter(Ticket.description.contains(IMPORT_MARK)).all()]
    if not ids:
        return 0
    for chunk in range(0, len(ids), 1000):
        part = ids[chunk:chunk + 1000]
        db.query(TicketComment).filter(TicketComment.ticket_id.in_(part)).delete(synchronize_session=False)
        db.query(TicketHistory).filter(TicketHistory.ticket_id.in_(part)).delete(synchronize_session=False)
        db.query(TicketAttachment).filter(TicketAttachment.ticket_id.in_(part)).delete(synchronize_session=False)
        db.query(Ticket).filter(Ticket.id.in_(part)).delete(synchronize_session=False)
    db.commit()
    return len(ids)


def run(path, replace=False, real_emails=False):
    dump = load_dump(path)
    tickets_src = sorted(dump['ticket'], key=lambda r: r[T_ID])
    db = SessionLocal()

    existing = db.query(Ticket).filter(Ticket.description.contains(IMPORT_MARK)).count()
    if existing and not replace:
        print(f"Ya hay {existing} tickets importados. Usa --replace para borrarlos e importar de nuevo.")
        return
    if replace:
        print(f"Borrados {delete_imported(db)} tickets importados antes.")

    random_hash = hash_password(secrets.token_urlsafe(24))
    used_emails = {u.email.lower() for u in db.query(User.email).all()}

    def make_email(real):
        real = (real or '').strip().lower()
        if real_emails and re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', real):
            return real
        local = re.sub(r'[^a-z0-9._-]', '', real.split('@')[0]) or 'usuario'
        email, n = f"{local}@{FAKE_DOMAIN}", 2
        while email in used_emails:
            email, n = f"{local}{n}@{FAKE_DOMAIN}", n + 1
        return email

    # --- Ubicaciones
    locations = {key(b.name): b for b in db.query(Location).all()}
    official = [clean(r[1]) for r in dump.get('ubicaciones', []) if clean(r[1]) and key(r[1]) != 'zz']

    def get_location(name):
        k = key(name)
        if k in LOCATION_ALIASES:
            if LOCATION_ALIASES[k] is None:
                return None
            name = LOCATION_ALIASES[k]
            k = key(name)
        if not k or k == 'zz':
            return None
        if k not in locations:
            pretty = next((o for o in official if key(o) == k), clean(name))
            if pretty.isupper():
                pretty = pretty.title()
            location = Location(name=pretty[:150], type=location_type(pretty), is_active=True)
            db.add(location)
            db.flush()
            locations[k] = location
        return locations[k]

    for name in official:
        get_location(name)

    # --- Técnicos
    users_by_email = {u.email.lower(): u for u in db.query(User).all()}
    staff_users = {}

    def get_staff(asesor):
        k = key(asesor)
        if not k:
            return None
        found = [(k.find(needle), who) for needle, who in ASESOR_KEYS if needle in k]
        person = min(found)[1] if found else None
        if person is None:
            person = 'otro_' + k
            STAFF[person] = (f"Técnico {clean(asesor).upper()}", None, False)
        if person not in staff_users:
            name, real_email, active = STAFF[person]
            user = users_by_email.get((real_email or '').lower())
            if user is None:
                slug = '.'.join(key(part) for part in name.split()[:2])
                email = make_email(real_email if real_emails and real_email else f"{slug}@empack.com.mx")
                user = User(name=name, email=email, password_hash=random_hash,
                            role='support', is_active=active)
                db.add(user)
                db.flush()
                used_emails.add(email)
                users_by_email[email] = user
            staff_users[person] = user
        return staff_users[person]

    # --- Usuarios que levantaron tickets (uno por correo; nombre y ubicación más frecuentes)
    names_by_email = defaultdict(Counter)
    location_by_email = defaultdict(Counter)
    for r in tickets_src:
        ident = clean(r[T_EMAIL]).lower() or key(r[T_NOMBRE])
        if not ident:
            continue
        if clean(r[T_NOMBRE]):
            names_by_email[ident][title_name(r[T_NOMBRE])] += 1
        if key(r[T_UBIC]):
            location_by_email[ident][clean(r[T_UBIC])] += 1

    requesters = {}

    def get_requester(r):
        ident = clean(r[T_EMAIL]).lower() or key(r[T_NOMBRE])
        if not ident:
            return None
        if ident not in requesters:
            user = users_by_email.get(ident) if real_emails else None
            if user is None:
                name = names_by_email[ident].most_common(1)[0][0] if names_by_email[ident] else ident.split('@')[0]
                email = make_email(ident if '@' in ident else f"{ident}@empack.com.mx")
                top_location = location_by_email[ident].most_common(1)
                location = get_location(top_location[0][0]) if top_location else None
                user = User(name=name[:150], email=email, password_hash=random_hash, role='user',
                            location_id=location.id if location else None, is_active=True)
                db.add(user)
                db.flush()
                used_emails.add(email)
            requesters[ident] = user
        return requesters[ident]

    # --- Catálogo
    incidencias = {key(i.name): i for i in db.query(Incidencia).all()}
    subs = {(s.incidencia_id, key(s.name)): s for s in db.query(Subincidencia).all()}
    asunto_fix = fix_truncated([clean(r[T_ASUNTO]) for r in tickets_src])
    tipo_fix = fix_truncated([clean(r[T_TIPO]) for r in tickets_src])

    def get_category(r):
        asunto = clean(r[T_ASUNTO])
        asunto = asunto_fix.get(asunto, asunto)
        k = key(asunto)
        name, default_sub = 'Otros', None
        for prefixes, inc_name, sub_name in CATEGORY_RULES:
            if any(k == key(p) or (len(key(p)) > 2 and k.startswith(key(p))) for p in prefixes):
                name, default_sub = inc_name, sub_name
                break
        if key(name) not in incidencias:
            inc = Incidencia(name=name, is_active=True)
            db.add(inc)
            db.flush()
            incidencias[key(name)] = inc
        inc = incidencias[key(name)]

        tipo = clean(r[T_TIPO])
        tipo = tipo_fix.get(tipo, tipo)
        if len(key(tipo)) < 2:
            tipo = default_sub or 'General'
        tipo = tipo[:1].upper() + tipo[1:100]
        sk = (inc.id, key(tipo))
        if sk not in subs:
            sub = Subincidencia(incidencia_id=inc.id, name=tipo, is_active=True)
            db.add(sub)
            db.flush()
            subs[sk] = sub
        return inc, subs[sk]

    # --- Chat agrupado por ticket
    chat_by_ticket = defaultdict(list)
    for c in dump.get('chat', []):
        chat_by_ticket[c[3]].append(c)

    def to_utc_created(r, local_dt):
        return local_dt if r[T_ID] >= UTC_FROM_TICKET_ID else local_dt + MX_OFFSET

    def chat_offset(r):
        # El chat sigue la misma regla que la fecha del ticket
        return timedelta(0) if r[T_ID] >= UTC_FROM_TICKET_ID else MX_OFFSET

    stats = Counter()
    last_created = None

    for r in tickets_src:
        created_local = parse_local(r[T_FECHA])
        if created_local is not None:
            created = to_utc_created(r, created_local)
            stats['fecha_ok'] += 1
        else:
            chat_dates = [parse_chat_date(c[5], last_created) for c in chat_by_ticket.get(r[T_ID], [])]
            chat_dates = [d for d in chat_dates if d]
            resp = parse_local(r[T_RESPUESTA], date_only_hour=18)
            if chat_dates:
                created = min(chat_dates) + chat_offset(r)
                stats['fecha_de_chat'] += 1
            elif resp:
                created = resp + MX_OFFSET
                stats['fecha_de_respuesta'] += 1
            elif last_created:
                created = last_created
                stats['fecha_aproximada'] += 1
            else:
                stats['sin_fecha_omitido'] += 1
                continue
        last_created = created

        requester = get_requester(r)
        staff = get_staff(r[T_ASESOR])
        inc, sub = get_category(r)
        location = get_location(r[T_UBIC]) or (
            db.get(Location, requester.location_id) if requester and requester.location_id else None
        )

        estado = clean(r[T_ESTADO])
        status = STATUS_MAP.get(estado, 'open')
        message = clean_message = (r[T_MENSAJE] or '').strip()
        upper = clean_message.upper()
        priority = 'urgent' if ('MUY URGENTE' in upper or 'URGENTÍSIMO' in upper or 'URGENTISIMO' in upper) \
            else 'high' if 'URGENTE' in upper else 'medium'
        if not message:
            message = f"{clean(r[T_ASUNTO])} - {clean(r[T_TIPO])}".strip(' -') or 'Sin descripción'
        description = f"{message}\n\n{IMPORT_MARK} (folio {clean(r[T_SERIE])})"

        resolved = None
        if status == 'closed':
            resp = parse_local(r[T_RESPUESTA], date_only_hour=18)
            if resp is not None:
                resp = resp + MX_OFFSET
                if resp >= created:
                    resolved = resp
            if resolved is None:
                staff_msgs = [parse_chat_date(c[5], created) for c in chat_by_ticket.get(r[T_ID], []) if c[1] == 0]
                staff_msgs = [d + chat_offset(r) for d in staff_msgs if d]
                staff_msgs = [d for d in staff_msgs if d >= created]
                if staff_msgs:
                    resolved = max(staff_msgs)
            stats['resuelto_con_fecha' if resolved else 'resuelto_sin_fecha'] += 1

        ticket = Ticket(
            incidencia_id=inc.id,
            subincidencia_id=sub.id,
            created_by_user_id=requester.id if requester else None,
            assigned_to_user_id=staff.id if staff else None,
            location_id=location.id if location else None,
            description=description,
            status=status,
            priority=priority,
            created_at=created,
            updated_at=resolved or created,
        )
        db.add(ticket)
        db.flush()
        stats['tickets'] += 1

        history = [TicketHistory(ticket_id=ticket.id, user_id=ticket.created_by_user_id, action='CREATE',
                                 old_value=None, new_value='Ticket creado', created_at=created)]
        if staff:
            history.append(TicketHistory(ticket_id=ticket.id, user_id=staff.id, action='ASSIGN',
                                         old_value=None, new_value=str(staff.id), created_at=created))
        if status == 'pending':
            history.append(TicketHistory(ticket_id=ticket.id, user_id=staff.id if staff else None,
                                         action='STATUS', old_value='in_progress', new_value='pending',
                                         created_at=created))
        if status == 'closed':
            when = resolved or created
            if resolved:
                history.append(TicketHistory(ticket_id=ticket.id, user_id=staff.id if staff else None,
                                             action='STATUS', old_value='in_progress', new_value='resolved',
                                             created_at=resolved))
            history.append(TicketHistory(ticket_id=ticket.id, user_id=staff.id if staff else None,
                                         action='CLOSE', old_value='resolved', new_value='closed',
                                         created_at=when))
        db.add_all(history)

        # Conversación
        for c in sorted(chat_by_ticket.get(r[T_ID], []), key=lambda c: c[0]):
            body = (c[4] or '').strip()
            if body.startswith('SOPORTE EMPACK, Esta procesando'):
                continue
            if not body and c[6]:
                body = f"[Archivo adjunto en el sistema anterior: {os.path.basename(c[6])}]"
            if not body:
                continue
            when = parse_chat_date(c[5], created - chat_offset(r))
            when = (when + chat_offset(r)) if when else created
            author = staff if c[1] == 0 else requester
            db.add(TicketComment(ticket_id=ticket.id, user_id=author.id if author else None,
                                 body=body, is_internal=False, created_at=when))
            stats['comentarios'] += 1

        solution = (r[T_SOLUCION] or '').strip()
        if len(key(solution)) > 2 and staff:
            db.add(TicketComment(ticket_id=ticket.id, user_id=staff.id, body=f"Solución: {solution}",
                                 is_internal=False, created_at=resolved or created))
            stats['soluciones'] += 1

        if stats['tickets'] % 500 == 0:
            db.commit()
            print(f"  {stats['tickets']} tickets...")

    db.commit()
    print("Listo.")
    print(f"  Ubicaciones: {len(locations)}  Técnicos: {len(staff_users)}  Usuarios: {len(requesters)}")
    print(f"  Categorías: {len(incidencias)}  Subcategorías: {len(subs)}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    db.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], replace='--replace' in sys.argv, real_emails='--real-emails' in sys.argv)
