from fastapi import HTTPException

from db.connection import get_connection
from services.sql_fragments import DISPATCH_SELECT, fetch_dispatch
from sockets import manager as socket

ALLOWED_STATUSES = ("sent", "acknowledged", "en-route", "on-site", "resolved")


def list_dispatches(status, tech_id, dispatched_by, page: int, limit: int) -> dict:
    offset = (page - 1) * limit
    conditions, params = [], []
    if status:
        conditions.append("d.status = %s")
        params.append(status)
    if tech_id:
        conditions.append("d.tech_id = %s")
        params.append(int(tech_id))
    if dispatched_by:
        conditions.append("d.dispatched_by = %s")
        params.append(int(dispatched_by))

    where_sql = " AND ".join(conditions) if conditions else "TRUE"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                DISPATCH_SELECT + f" WHERE {where_sql} ORDER BY d.dispatched_at DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            dispatches = cur.fetchall()

            cur.execute(f"SELECT COUNT(*) AS count FROM dispatches d WHERE {where_sql}", params)
            total = cur.fetchone()["count"]
    finally:
        conn.close()

    return {"dispatches": dispatches, "total": total, "page": page, "limit": limit}


def get_dispatch(dispatch_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            dispatch = fetch_dispatch(cur, dispatch_id)
    finally:
        conn.close()

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    return {"dispatch": dispatch}


async def create_dispatch(user: dict, job_id: int | None, tech_id: int | None, dispatch_notes: str | None) -> dict:
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
            job = cur.fetchone()
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            cur.execute(
                """
                INSERT INTO dispatches (job_id, tech_id, dispatched_by, dispatch_notes)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (job_id, tech_id, user["id"], dispatch_notes),
            )
            dispatch_id = cur.fetchone()["id"]

            if tech_id:
                cur.execute(
                    "UPDATE jobs SET status = 'assigned', assigned_tech_id = %s, updated_at = now() WHERE id = %s",
                    (tech_id, job_id),
                )

            conn.commit()
            dispatch = fetch_dispatch(cur, dispatch_id)
    finally:
        conn.close()

    await socket.emit_dispatch_new(dispatch, dict(job))
    return {"dispatch": dispatch}


async def update_dispatch_status(dispatch_id: int, status: str | None) -> dict:
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of: {', '.join(ALLOWED_STATUSES)}")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE dispatches SET status = %s, updated_at = now() WHERE id = %s RETURNING id",
                (status, dispatch_id),
            )
            updated = cur.fetchone()
            conn.commit()
    finally:
        conn.close()

    if not updated:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    await socket.emit_dispatch_status(dispatch_id, status)
    return {"message": "Status updated", "dispatchId": dispatch_id, "status": status}
