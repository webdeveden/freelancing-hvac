from typing import Optional

from pydantic import BaseModel


class CreateDispatchRequest(BaseModel):
    job_id: Optional[int] = None
    tech_id: Optional[int] = None
    dispatch_notes: Optional[str] = None


class UpdateDispatchStatusRequest(BaseModel):
    status: Optional[str] = None
