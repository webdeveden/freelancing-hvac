"""
job.py — Pydantic model for the job payload sent to the Node.js backend.
"""

from typing   import Optional
from pydantic import BaseModel


class JobPayload(BaseModel):
    caller_name:   Optional[str] = None
    caller_phone:  str
    service_type:  Optional[str] = None
    description:   Optional[str] = None
    address:       Optional[str] = None
    city:          Optional[str] = None
    priority:      str = "normal"        # 'normal' | 'high' | 'emergency'
    call_sid:      Optional[str] = None
    scheduled_at:  Optional[str] = None
