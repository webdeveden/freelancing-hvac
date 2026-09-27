from fastapi import APIRouter, HTTPException, Request

from config.settings import settings
from db.connection import get_connection
from models.internal import InternalJobNotifyRequest
from services.sql_fragments import fetch_job
from sockets import manager as socket

router = APIRouter()


@router.post("/jobs", status_code=201)
async def notify_job(body: InternalJobNotifyRequest, request: Request):
    secret = request.headers.get("x-internal-secret")
    if not secret or secret != settings.internal_api_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not body.job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            job = fetch_job(cur, body.job_id)
    finally:
        conn.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await socket.emit_job_created(job)
    if job["priority"] == "emergency":
        await socket.emit_emergency_alert(job)

    return {"job": job}
