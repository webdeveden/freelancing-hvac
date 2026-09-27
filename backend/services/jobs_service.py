from datetime import datetime

from fastapi import HTTPException

from db.connection import get_connection
from services.sql_fragments import JOB_SELECT, fetch_job, fetch_dispatch
from sockets import manager as socket


def _parse_datetime(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_job_where(user: dict, status, priority, assigned_tech_id, source):
    """Mirrors the Prisma `where` object built in jobs.controller.js#listJobs."""
    filters: dict[str, tuple[str, object | None]] = {}

    if status:
        filters["status"] = ("j.status = %s", status)
    if priority:
        filters["priority"] = ("j.priority = %s", priority)
    if assigned_tech_id:
        filters["assigned_tech_id"] = ("j.assigned_tech_id = %s", int(assigned_tech_id))
    if source == "ai":
        filters["call_sid"] = ("j.call_sid IS NOT NULL", None)
    elif source == "manual":
        filters["call_sid"] = ("j.call_sid IS NULL", None)

    or_clause = None

    if user["role"] == "tech":
        if assigned_tech_id:
            filters["assigned_tech_id"] = ("j.assigned_tech_id = %s", user["id"])
        elif status in ("in-progress", "completed"):
            filters["assigned_tech_id"] = ("j.assigned_tech_id = %s", user["id"])
        elif status == "requested":
            filters["requested_by_id"] = ("j.requested_by_id = %s", user["id"])
        elif not status:
            or_clause = (
                "(j.status = %s OR (j.status = %s AND j.requested_by_id = %s))",
                ["pending", "requested", user["id"]],
            )

    conditions, params = [], []
    for sql, param in filters.values():
        conditions.append(sql)
        if param is not None:
            params.append(param)
    if or_clause:
        conditions.append(or_clause[0])
        params.extend(or_clause[1])

    return (" AND ".join(conditions) if conditions else "TRUE"), params


def _status_count_where(user: dict):
    if user["role"] == "tech":
        return (
            "(status = %s OR assigned_tech_id = %s OR (status = %s AND requested_by_id = %s))",
            ["pending", user["id"], "requested", user["id"]],
        )
    return "TRUE", []


def list_jobs(user: dict, status, priority, assigned_tech_id, source, page: int, limit: int) -> dict:
    offset = (page - 1) * limit
    where_sql, params = _build_job_where(user, status, priority, assigned_tech_id, source)
    count_where_sql, count_params = _status_count_where(user)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                JOB_SELECT + f" WHERE {where_sql} ORDER BY j.created_at DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            jobs = cur.fetchall()

            cur.execute(f"SELECT COUNT(*) AS count FROM jobs j WHERE {where_sql}", params)
            total = cur.fetchone()["count"]

            cur.execute(
                f"SELECT status, COUNT(*) AS count FROM jobs WHERE {count_where_sql} GROUP BY status",
                count_params,
            )
            status_counts = {row["status"]: row["count"] for row in cur.fetchall()}
    finally:
        conn.close()

    return {"jobs": jobs, "total": total, "page": page, "limit": limit, "statusCounts": status_counts}


def get_job(job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}


async def create_job(body) -> dict:
    if not body.caller_phone:
        raise HTTPException(status_code=400, detail="caller_phone is required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO jobs
                    (caller_name, caller_phone, service_type, description, address, city,
                     status, priority, scheduled_at, notes, call_sid)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    body.caller_name,
                    body.caller_phone,
                    body.service_type,
                    body.description,
                    body.address,
                    body.city,
                    body.status or "pending",
                    body.priority or "normal",
                    _parse_datetime(body.scheduled_at),
                    body.notes,
                    body.call_sid,
                ),
            )
            job_id = cur.fetchone()["id"]
            conn.commit()
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    await socket.emit_job_created(job)
    if job["priority"] == "emergency":
        await socket.emit_emergency_alert(job)

    return {"job": job}


_TECH_ALLOWED_FIELDS = {"status"}
_ADMIN_ALLOWED_FIELDS = {
    "status", "priority", "service_type", "description", "address", "city",
    "assigned_tech_id", "scheduled_at", "notes",
}


async def update_job(user: dict, job_id: int, body) -> dict:
    is_admin = user["role"] == "admin"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if user["role"] == "tech":
                cur.execute("SELECT assigned_tech_id FROM jobs WHERE id = %s", (job_id,))
                existing = cur.fetchone()
                if not existing:
                    raise HTTPException(status_code=404, detail="Job not found")
                if existing["assigned_tech_id"] != user["id"]:
                    raise HTTPException(status_code=403, detail="You can only update status on jobs assigned to you")

            allowed = _ADMIN_ALLOWED_FIELDS if is_admin else _TECH_ALLOWED_FIELDS
            raw = body.model_dump(exclude_unset=True)
            data = {k: v for k, v in raw.items() if k in allowed}

            if not data:
                raise HTTPException(status_code=400, detail="No updatable fields provided")

            if "scheduled_at" in data:
                data["scheduled_at"] = _parse_datetime(data["scheduled_at"])

            # Setting status back to 'pending' on an already-assigned job keeps it
            # 'assigned' so it stays under the tech's queue.
            if data.get("status") == "pending":
                cur.execute("SELECT assigned_tech_id FROM jobs WHERE id = %s", (job_id,))
                current = cur.fetchone()
                if current and current["assigned_tech_id"]:
                    data["status"] = "assigned"

            set_clause = ", ".join(f"{key} = %s" for key in data)
            cur.execute(
                f"UPDATE jobs SET {set_clause}, updated_at = now() WHERE id = %s RETURNING id",
                (*data.values(), job_id),
            )
            updated = cur.fetchone()
            if not updated:
                raise HTTPException(status_code=404, detail="Job not found")
            conn.commit()
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    await socket.emit_job_updated(job)
    return {"job": job}


async def assign_tech(user: dict, job_id: int, tech_id: int | None) -> dict:
    if not tech_id:
        raise HTTPException(status_code=400, detail="tech_id is required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE id = %s AND role = 'tech' AND is_active = true",
                (tech_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Technician not found")

            cur.execute(
                "UPDATE jobs SET assigned_tech_id = %s, status = 'assigned', updated_at = now() WHERE id = %s RETURNING id",
                (tech_id, job_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Job not found")

            job = fetch_job(cur, job_id)

            cur.execute("SELECT id FROM dispatches WHERE job_id = %s", (job_id,))
            existing = cur.fetchone()

            new_dispatch = None
            if existing:
                cur.execute(
                    "UPDATE dispatches SET tech_id = %s, dispatched_by = %s, updated_at = now() WHERE id = %s",
                    (tech_id, user["id"], existing["id"]),
                )
            else:
                cur.execute(
                    "INSERT INTO dispatches (job_id, tech_id, dispatched_by) VALUES (%s, %s, %s) RETURNING id",
                    (job_id, tech_id, user["id"]),
                )
                dispatch_id = cur.fetchone()["id"]
                new_dispatch = fetch_dispatch(cur, dispatch_id)

            conn.commit()
    finally:
        conn.close()

    if new_dispatch:
        await socket.emit_dispatch_new(new_dispatch, job)
    await socket.emit_job_updated(job)
    return {"job": job}


async def unassign_tech(job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, assigned_tech_id FROM jobs WHERE id = %s", (job_id,))
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Job not found")
            if not existing["assigned_tech_id"]:
                raise HTTPException(status_code=400, detail="Job has no assigned technician")

            cur.execute(
                "UPDATE jobs SET assigned_tech_id = NULL, status = 'pending', updated_at = now() WHERE id = %s",
                (job_id,),
            )
            cur.execute("DELETE FROM dispatches WHERE job_id = %s", (job_id,))
            conn.commit()
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    await socket.emit_job_updated(job)
    return {"job": job}


async def delete_job(job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM jobs WHERE id = %s RETURNING id", (job_id,))
            deleted = cur.fetchone()
            conn.commit()
    finally:
        conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")

    await socket.emit_job_deleted(job_id)
    return {"message": "Job deleted", "jobId": job_id}


async def claim_job(user: dict, job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status, requested_by_id FROM jobs WHERE id = %s", (job_id,))
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Job not found")
            if existing["status"] != "pending":
                raise HTTPException(status_code=400, detail="Only pending jobs can be claimed")
            if existing["requested_by_id"]:
                raise HTTPException(status_code=409, detail="Job has already been claimed by another tech")

            cur.execute(
                "UPDATE jobs SET status = 'requested', requested_by_id = %s, updated_at = now() WHERE id = %s",
                (user["id"], job_id),
            )
            conn.commit()
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    await socket.emit_job_requested(job)
    return {"job": job}


async def approve_request(user: dict, job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status, requested_by_id FROM jobs WHERE id = %s", (job_id,))
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Job not found")
            if existing["status"] != "requested":
                raise HTTPException(status_code=400, detail="Job is not in requested status")

            cur.execute(
                "UPDATE jobs SET status = 'assigned', assigned_tech_id = %s, updated_at = now() WHERE id = %s",
                (existing["requested_by_id"], job_id),
            )
            cur.execute(
                "INSERT INTO dispatches (job_id, tech_id, dispatched_by) VALUES (%s, %s, %s)",
                (job_id, existing["requested_by_id"], user["id"]),
            )
            conn.commit()
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    await socket.emit_job_updated(job)
    return {"job": job}


async def reject_request(job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM jobs WHERE id = %s", (job_id,))
            existing = cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Job not found")
            if existing["status"] != "requested":
                raise HTTPException(status_code=400, detail="Job is not in requested status")

            cur.execute(
                "UPDATE jobs SET status = 'rejected', updated_at = now() WHERE id = %s",
                (job_id,),
            )
            conn.commit()
            job = fetch_job(cur, job_id)
    finally:
        conn.close()

    await socket.emit_job_updated(job)
    return {"job": job}


# ── Comments ───────────────────────────────────────────────────────────────

def get_comments(job_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.job_id, c.author_id, c.content, c.created_at, c.updated_at,
                       u.full_name AS author_name, u.role AS author_role
                FROM job_comments c
                JOIN users u ON u.id = c.author_id
                WHERE c.job_id = %s
                ORDER BY c.created_at ASC
                """,
                (job_id,),
            )
            comments = cur.fetchall()
    finally:
        conn.close()

    return {"comments": comments}


async def add_comment(user: dict, job_id: int, content: str | None) -> dict:
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Comment content is required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Job not found")

            cur.execute(
                "INSERT INTO job_comments (job_id, author_id, content) VALUES (%s, %s, %s) RETURNING id, created_at",
                (job_id, user["id"], content.strip()),
            )
            created = cur.fetchone()
            conn.commit()
    finally:
        conn.close()

    comment = {
        "id": created["id"],
        "job_id": job_id,
        "author_id": user["id"],
        "author_name": user["name"],
        "author_role": user["role"],
        "content": content.strip(),
        "created_at": created["created_at"],
    }

    await socket.emit_comment_added(job_id, comment)
    return {"comment": comment}


async def delete_comment(user: dict, job_id: int, comment_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT author_id FROM job_comments WHERE id = %s AND job_id = %s",
                (comment_id, job_id),
            )
            comment = cur.fetchone()
            if not comment:
                raise HTTPException(status_code=404, detail="Comment not found")

            is_owner = comment["author_id"] == user["id"]
            if user["role"] != "admin" and not is_owner:
                raise HTTPException(status_code=403, detail="Cannot delete another user's comment")

            cur.execute("DELETE FROM job_comments WHERE id = %s", (comment_id,))
            conn.commit()
    finally:
        conn.close()

    await socket.emit_comment_deleted(job_id, comment_id)
    return {"message": "Comment deleted", "commentId": comment_id}
