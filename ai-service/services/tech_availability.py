"""
tech_availability.py — Tool handler for check_tech_availability

Queries PostgreSQL for active technicians and their current workload.
A tech is "available" when they have zero active dispatches; "busy" when
they have one or more dispatches with status in (sent, acknowledged,
en_route, on_site).
"""

import psycopg2
import psycopg2.extras

from config.settings import settings


_ACTIVE_STATUSES = ("sent", "acknowledged", "en_route", "on_site")


def get_connection():
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


def get_available_techs() -> list[dict]:
    """
    Returns all active technicians sorted by current workload (least busy first).
    Each entry: {name, phone, active_jobs, status}
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                SELECT
                    u.full_name AS name,
                    u.phone,
                    COUNT(d.id) FILTER (
                        WHERE d.status = ANY(%s)
                    ) AS active_jobs
                FROM users u
                LEFT JOIN dispatches d ON d.tech_id = u.id
                WHERE u.role = 'tech' AND u.is_active = true
                GROUP BY u.id, u.full_name, u.phone
                ORDER BY active_jobs ASC, u.full_name ASC
                """,
                (_ACTIVE_STATUSES,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    techs = []
    for row in rows:
        active_jobs = row["active_jobs"]
        techs.append({
            "name": row["name"],
            "phone": row["phone"] or "N/A",
            "active_jobs": active_jobs,
            "status": "available" if active_jobs == 0 else "busy",
        })
    return techs
