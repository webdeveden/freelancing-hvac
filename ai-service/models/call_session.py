"""
call_session.py — Pydantic model for an active voice call session.

One session exists per active Twilio call (keyed by CallSid).
Stored in memory for the duration of the call — no DB persistence needed.
"""

from datetime import datetime
from typing   import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single turn in the conversation history (role + text)."""
    role:    str  # 'user' (caller speech) or 'assistant' (AI speech)
    content: str


class CallSession(BaseModel):
    call_sid:   str
    state:      str = "GREETING"
    # States: GREETING → COLLECTING_INFO → CONFIRMING → BOOKING → FAREWELL | FAQ

    # Caller data collected during the conversation
    caller_name:   Optional[str] = None
    caller_phone:  str = ""
    service_type:  Optional[str] = None
    address:       Optional[str] = None
    city:          Optional[str] = None
    description:   Optional[str] = None
    scheduled_at:  Optional[str] = None   # ISO string if caller specified a time
    is_emergency:  bool = False

    # Full conversation history sent to Claude on each gather turn
    conversation_history: List[Message] = Field(default_factory=list)

    # Retry counter — after 3 failed attempts in a state, we bail gracefully
    attempts: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
