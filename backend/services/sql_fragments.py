"""
sql_fragments.py — Shared SELECT projections

Raw-SQL equivalent of the Prisma `include` + format-function pairs used by
the old Node controllers, so both jobs_service and dispatches_service
produce identically-shaped JSON without duplicating the join logic.
"""

JOB_SELECT = """
    SELECT j.*,
           at.full_name AS assigned_tech_name,
           at.phone     AS assigned_tech_phone,
           rb.full_name AS requested_by_name
    FROM jobs j
    LEFT JOIN users at ON at.id = j.assigned_tech_id
    LEFT JOIN users rb ON rb.id = j.requested_by_id
"""

DISPATCH_SELECT = """
    SELECT d.*,
           j.caller_name  AS caller_name,
           j.caller_phone AS caller_phone,
           j.service_type AS service_type,
           j.address      AS address,
           j.city         AS city,
           j.status       AS job_status,
           j.priority     AS job_priority,
           t.full_name    AS tech_name,
           disp.full_name AS dispatched_by_name
    FROM dispatches d
    JOIN jobs j        ON j.id = d.job_id
    LEFT JOIN users t    ON t.id = d.tech_id
    LEFT JOIN users disp ON disp.id = d.dispatched_by
"""


def fetch_job(cur, job_id: int) -> dict | None:
    cur.execute(JOB_SELECT + " WHERE j.id = %s", (job_id,))
    return cur.fetchone()


def fetch_dispatch(cur, dispatch_id: int) -> dict | None:
    cur.execute(DISPATCH_SELECT + " WHERE d.id = %s", (dispatch_id,))
    return cur.fetchone()
