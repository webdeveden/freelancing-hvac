from typing import Optional

from pydantic import BaseModel


class InternalJobNotifyRequest(BaseModel):
    job_id: Optional[int] = None
