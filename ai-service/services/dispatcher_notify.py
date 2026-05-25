"""
dispatcher_notify.py — Notifies the Node.js backend after a job is created

The Node.js backend broadcasts the new job to all connected dispatcher clients
via Socket.IO. We call its internal endpoint with a shared secret header.

This is intentionally separate from job_creator.py — the job is written to the
DB first (so it's durable), then we notify (which can fail without data loss).
"""

import httpx
from config.settings import settings


async def notify_job_created(job: dict) -> bool:
    """
    POSTs the job to the Node.js /api/internal/jobs endpoint.
    Returns True on success, False on any error (non-fatal — the job is already in DB).
    """
    url = f"{settings.backend_url}/api/internal/jobs"
    headers = {
        "Content-Type":    "application/json",
        "X-Internal-Secret": settings.internal_api_secret,
    }

    payload = {
        "job_id": job.get("id"),
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 201:
                return True
            print(f"[dispatcher_notify] Backend returned {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[dispatcher_notify] Failed to notify backend: {e}")
        return False
