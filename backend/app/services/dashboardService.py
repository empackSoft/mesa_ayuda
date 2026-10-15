from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.ticket import Ticket
from models.user import User
from models.ticketHistory import TicketHistory
from models.incidencia import Incidencia


def get_status_counts(db: Session):
    rows = (
        db.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )

    return {status: count for status, count in rows}


# Solo tickets abiertos (sin cerrar): es la carga de trabajo pendiente
def get_priority_counts(db: Session):
    rows = (
        db.query(Ticket.priority, func.count(Ticket.id))
        .filter(Ticket.status != "closed")
        .group_by(Ticket.priority)
        .all()
    )

    return {priority: count for priority, count in rows}


def get_performance_by_technician(db: Session):
    # Tickets asignados agrupados por técnico y estado
    rows = (
        db.query(
            User.id,
            User.name,
            Ticket.status,
            func.count(Ticket.id)
        )
        .join(Ticket, Ticket.assigned_to_user_id == User.id)
        .group_by(User.id, User.name, Ticket.status)
        .all()
    )

    result = {}

    for user_id, name, status, count in rows:
        if user_id not in result:
            result[user_id] = {
                "user_id": user_id,
                "name": name,
                "total": 0,
                "by_status": {}
            }

        result[user_id]["by_status"][status] = count
        result[user_id]["total"] += count

    return list(result.values())


def _resolution_durations(db: Session):
    """
    Devuelve una lista de tuplas:
    (ticket_id, priority, assigned_to_user_id, technician_name, seconds)
    tomando el PRIMER paso a 'resolved' de cada ticket.
    """
    # Primer evento 'resolved' por ticket (MIN del created_at del historial)
    first_resolved = (
        db.query(
            TicketHistory.ticket_id,
            func.min(TicketHistory.created_at).label("resolved_at")
        )
        .filter(
            TicketHistory.action == "STATUS",
            TicketHistory.new_value == "resolved"
        )
        .group_by(TicketHistory.ticket_id)
        .subquery()
    )

    rows = (
        db.query(
            Ticket.id,
            Ticket.priority,
            Ticket.assigned_to_user_id,
            User.name,
            Ticket.created_at,
            first_resolved.c.resolved_at
        )
        .join(first_resolved, first_resolved.c.ticket_id == Ticket.id)
        .outerjoin(User, User.id == Ticket.assigned_to_user_id)
        .all()
    )

    durations = []

    for ticket_id, priority, tech_id, tech_name, created_at, resolved_at in rows:
        if created_at and resolved_at:
            # Normalizar ambas fechas a naive (sin zona horaria)
            if created_at.tzinfo is not None:
                created_at = created_at.replace(tzinfo=None)
            if resolved_at.tzinfo is not None:
                resolved_at = resolved_at.replace(tzinfo=None)

            seconds = (resolved_at - created_at).total_seconds()
            if seconds >= 0:
                durations.append(
                    (ticket_id, priority, tech_id, tech_name, seconds)
                )

    return durations


def _avg_seconds(seconds_list):
    if not seconds_list:
        return None
    avg = sum(seconds_list) / len(seconds_list)
    return round(avg)


def get_resolution_times(db: Session):
    durations = _resolution_durations(db)

    all_seconds = [d[4] for d in durations]

    # Por prioridad
    by_priority = {}
    for _, priority, _, _, seconds in durations:
        by_priority.setdefault(priority, []).append(seconds)

    by_priority_avg = {
        priority: _avg_seconds(secs)
        for priority, secs in by_priority.items()
    }

    # Por técnico
    by_tech = {}
    for _, _, tech_id, tech_name, seconds in durations:
        key = tech_id if tech_id is not None else 0
        if key not in by_tech:
            by_tech[key] = {
                "user_id": tech_id,
                "name": tech_name if tech_name else "Sin asignar",
                "seconds": []
            }
        by_tech[key]["seconds"].append(seconds)

    by_technician_avg = [
        {
            "user_id": v["user_id"],
            "name": v["name"],
            "avg_resolution_seconds": _avg_seconds(v["seconds"]),
            "resolved_count": len(v["seconds"])
        }
        for v in by_tech.values()
    ]

    return {
        "average_seconds_general": _avg_seconds(all_seconds),
        "total_resolved": len(all_seconds),
        "by_priority": by_priority_avg,
        "by_technician": by_technician_avg
    }

# Las fechas se guardan en UTC; los días se agrupan en hora de México (UTC-6, sin horario de verano)
LOCAL_OFFSET = timedelta(hours=-6)
TREND_DAYS = 90


def get_ticket_trend(db: Session, days: int = TREND_DAYS):
    """
    Tickets creados y resueltos por día en los últimos `days` días.
    Resuelto = primer paso a 'resolved' del historial (igual que los tiempos de resolución).
    Devuelve todos los días, aunque tengan 0.
    """
    today = (datetime.utcnow() + LOCAL_OFFSET).date()
    first_day = today - timedelta(days=days - 1)
    since = datetime.combine(first_day, datetime.min.time()) - LOCAL_OFFSET

    created_rows = (
        db.query(Ticket.created_at)
        .filter(Ticket.created_at >= since)
        .all()
    )

    resolved_rows = (
        db.query(func.min(TicketHistory.created_at))
        .filter(
            TicketHistory.action == "STATUS",
            TicketHistory.new_value == "resolved"
        )
        .group_by(TicketHistory.ticket_id)
        .having(func.min(TicketHistory.created_at) >= since)
        .all()
    )

    def local_day(value):
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return (value + LOCAL_OFFSET).date()

    days_map = {
        first_day + timedelta(days=i): {"created": 0, "resolved": 0}
        for i in range(days)
    }

    for (created_at,) in created_rows:
        day = local_day(created_at)
        if day in days_map:
            days_map[day]["created"] += 1

    for (resolved_at,) in resolved_rows:
        day = local_day(resolved_at)
        if day in days_map:
            days_map[day]["resolved"] += 1

    return [
        {"date": day.isoformat(), **counts}
        for day, counts in days_map.items()
    ]


def _to_local(value):
    if value.tzinfo is not None:
        value = value.replace(tzinfo=None)
    return value + LOCAL_OFFSET


def get_category_counts(db: Session):
    """Tickets por categoría (incidencia): total y cuántos siguen sin cerrar."""
    rows = (
        db.query(
            Incidencia.id,
            Incidencia.name,
            Ticket.status,
            func.count(Ticket.id)
        )
        .join(Ticket, Ticket.incidencia_id == Incidencia.id)
        .group_by(Incidencia.id, Incidencia.name, Ticket.status)
        .all()
    )

    result = {}

    for incidencia_id, name, status, count in rows:
        item = result.setdefault(
            incidencia_id,
            {"incidencia_id": incidencia_id, "name": name, "total": 0, "open": 0}
        )
        item["total"] += count
        if status != "closed":
            item["open"] += count

    return sorted(result.values(), key=lambda i: i["total"], reverse=True)


def get_activity_heatmap(db: Session, days: int = TREND_DAYS):
    """
    Tickets creados por día de la semana y hora (hora de México), últimos `days` días.
    Devuelve celdas con valor: [{weekday: 0=lunes..6=domingo, hour: 0..23, count}]
    """
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(Ticket.created_at)
        .filter(Ticket.created_at >= since)
        .all()
    )

    cells = {}

    for (created_at,) in rows:
        local = _to_local(created_at)
        key = (local.weekday(), local.hour)
        cells[key] = cells.get(key, 0) + 1

    return [
        {"weekday": weekday, "hour": hour, "count": count}
        for (weekday, hour), count in sorted(cells.items())
    ]


# Rangos de antigüedad (en horas) para los tickets que siguen sin resolver
AGING_BUCKETS = [
    ("lt_1d", 24),
    ("1_3d", 72),
    ("3_7d", 168),
    ("1_4w", 672),
    ("gt_4w", None),
]


def get_open_aging(db: Session):
    """Tickets sin resolver (open, in_progress, pending) agrupados por antigüedad."""
    rows = (
        db.query(Ticket.created_at)
        .filter(Ticket.status.in_(["open", "in_progress", "pending"]))
        .all()
    )

    now = datetime.utcnow()
    counts = {key: 0 for key, _ in AGING_BUCKETS}

    for (created_at,) in rows:
        if created_at.tzinfo is not None:
            created_at = created_at.replace(tzinfo=None)
        hours = (now - created_at).total_seconds() / 3600
        for key, limit in AGING_BUCKETS:
            if limit is None or hours < limit:
                counts[key] += 1
                break

    return counts


def get_dashboard(db: Session):
    return {
        "category_counts": get_category_counts(db),
        "activity_heatmap": get_activity_heatmap(db),
        "open_aging": get_open_aging(db),
        "trend": get_ticket_trend(db),
        "status_counts": get_status_counts(db),
        "priority_counts": get_priority_counts(db),
        "performance_by_technician": get_performance_by_technician(db),
        "resolution_times": get_resolution_times(db)
    }