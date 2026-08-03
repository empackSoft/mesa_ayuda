from sqlalchemy.orm import Session
from sqlalchemy import func

from models.ticket import Ticket
from models.user import User
from models.ticketHistory import TicketHistory


def get_status_counts(db: Session):
    rows = (
        db.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )

    return {status: count for status, count in rows}


def get_priority_counts(db: Session):
    rows = (
        db.query(Ticket.priority, func.count(Ticket.id))
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

def get_dashboard(db: Session):
    return {
        "status_counts": get_status_counts(db),
        "priority_counts": get_priority_counts(db),
        "performance_by_technician": get_performance_by_technician(db),
        "resolution_times": get_resolution_times(db)
    }