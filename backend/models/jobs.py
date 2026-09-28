from typing import Optional

from pydantic import BaseModel


class CreateJobRequest(BaseModel):
    caller_name: Optional[str] = None
    caller_phone: Optional[str] = None
    service_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None
    call_sid: Optional[str] = None


class UpdateJobRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    service_type: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    assigned_tech_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None


class AssignTechRequest(BaseModel):
    tech_id: Optional[int] = None


class AddCommentRequest(BaseModel):
    content: Optional[str] = None
