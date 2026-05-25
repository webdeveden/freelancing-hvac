"""
call_state.py — In-memory call session store

Sessions are keyed by Twilio CallSid and live only for the duration of a call.
Thread-safe via a simple dict with asyncio — FastAPI is single-threaded per worker,
so no locking is needed for this use case.

For multi-worker production deployments, swap this dict for Redis.
"""

from typing import Dict, Optional
from models.call_session import CallSession


# Keyed by call_sid (Twilio's unique identifier per call)
_sessions: Dict[str, CallSession] = {}


def create_session(call_sid: str, caller_phone: str) -> CallSession:
    session = CallSession(call_sid=call_sid, caller_phone=caller_phone)
    _sessions[call_sid] = session
    return session


def get_session(call_sid: str) -> Optional[CallSession]:
    return _sessions.get(call_sid)


def update_session(session: CallSession) -> None:
    _sessions[session.call_sid] = session


def delete_session(call_sid: str) -> None:
    _sessions.pop(call_sid, None)


def active_count() -> int:
    return len(_sessions)
