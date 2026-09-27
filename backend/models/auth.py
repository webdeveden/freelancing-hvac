from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None


class RegisterRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
