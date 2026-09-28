"""
manager.py — Socket.IO server (python-socketio) + emit helpers

Protocol-compatible with the `socket.io-client` the Vue frontend already
uses (frontend/src/composables/useSocket.js) — no frontend changes needed.

Mirrors backend/src/services/socket.service.js (emit helpers) and
backend/src/socket/handlers.js (connection event handlers).
"""

import jwt
import socketio
from fastapi.encoders import jsonable_encoder

from auth.security import decode_token
from config.settings import settings

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[settings.frontend_url, "http://localhost:5173"],
)

DISPATCHERS_ROOM = "dispatchers"


@sio.on("join:dispatchers")
async def join_dispatchers(sid, data=None):
    token = (data or {}).get("token")
    if not token:
        await sio.emit("error", {"message": "Token required to join dispatchers room"}, to=sid)
        return

    try:
        user = decode_token(token)
    except jwt.PyJWTError:
        await sio.emit("error", {"message": "Invalid or expired token"}, to=sid)
        return

    await sio.save_session(sid, {"user": user})
    await sio.enter_room(sid, DISPATCHERS_ROOM)
    await sio.emit("joined", {"room": DISPATCHERS_ROOM, "user": {"id": user["id"], "role": user["role"]}}, to=sid)
    print(f"[socket] User {user['id']} ({user['role']}) joined dispatchers")


@sio.on("dispatch:acknowledge")
async def dispatch_acknowledge(sid, data=None):
    session = await sio.get_session(sid)
    user = session.get("user") if session else None
    if not user:
        return
    dispatch_id = (data or {}).get("dispatchId")
    await sio.emit(
        "dispatch:acknowledged",
        {"dispatchId": dispatch_id, "by": user["id"]},
        room=DISPATCHERS_ROOM,
        skip_sid=sid,
    )


@sio.on("connect")
async def connect(sid, environ):
    print(f"[socket] New connection: {sid}")


@sio.on("disconnect")
async def disconnect(sid):
    session = await sio.get_session(sid)
    user = session.get("user") if session else None
    if user:
        print(f"[socket] User {user['id']} disconnected")


async def _emit(event: str, data: dict):
    """Runs the payload through FastAPI's encoder first (datetime -> ISO string, etc.) —
    python-socketio's own JSON encoder, unlike FastAPI's HTTP responses, doesn't handle those."""
    await sio.emit(event, jsonable_encoder(data), room=DISPATCHERS_ROOM)


# ── Job events ─────────────────────────────────────────────────────────────

async def emit_job_created(job: dict):
    await _emit("job:created", {"job": job})


async def emit_job_requested(job: dict):
    await _emit("job:requested", {"job": job})


async def emit_job_updated(job: dict):
    await _emit("job:updated", {"job": job})


async def emit_job_deleted(job_id: int):
    await _emit("job:deleted", {"jobId": job_id})


# ── Dispatch events ────────────────────────────────────────────────────────

async def emit_dispatch_new(dispatch: dict, job: dict):
    await _emit("dispatch:new", {"dispatch": dispatch, "job": job})


async def emit_dispatch_status(dispatch_id: int, status_: str):
    await _emit("dispatch:status", {"dispatchId": dispatch_id, "status": status_})


# ── Emergency alert ────────────────────────────────────────────────────────

async def emit_emergency_alert(job: dict):
    message = f"EMERGENCY: {job.get('service_type') or 'HVAC Emergency'} at {job.get('address')}, {job.get('city') or ''}".strip()
    await _emit("emergency:alert", {"job": job, "message": message})


# ── Comment events ─────────────────────────────────────────────────────────

async def emit_comment_added(job_id: int, comment: dict):
    await _emit("comment:added", {"jobId": job_id, "comment": comment})


async def emit_comment_deleted(job_id: int, comment_id: int):
    await _emit("comment:deleted", {"jobId": job_id, "commentId": comment_id})
