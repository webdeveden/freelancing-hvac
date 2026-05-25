"""
job_creator.py — Inserts a completed booking into PostgreSQL

Called after the AI confirms the caller's details and transitions to BOOKING state.
Creates the job record directly (not via the Node.js REST API) for speed,
then calls dispatcher_notify to trigger the real-time Socket.IO broadcast.
"""

import psycopg2
import psycopg2.extras
from config.settings import settings
from models.job       import JobPayload


def get_connection():
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


def create_job(payload: JobPayload) -> dict:
    """
    Inserts a new job row and returns the full job dict.
    Raises on DB error — caller should handle and fall back to a graceful TwiML response.
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                """
                INSERT INTO jobs
                  (caller_name, caller_phone, service_type, description,
                   address, city, status, priority, call_sid, scheduled_at)
                VALUES (%s,%s,%s,%s,%s,%s,'pending',%s,%s,%s)
                RETURNING *
                """,
                (
                    payload.caller_name,
                    payload.caller_phone,
                    payload.service_type,
                    payload.description,
                    payload.address,
                    payload.city,
                    payload.priority,
                    payload.call_sid,
                    payload.scheduled_at,
                )
            )
            job = dict(cur.fetchone())
        conn.commit()
        return job
    finally:
        conn.close()
