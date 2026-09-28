"""
dependencies.py — FastAPI auth dependencies

Equivalent to the old Express middleware (backend/src/middleware/auth.js):
  requireAuth              -> get_current_user
  requireAdmin             -> require_admin
  requireAdminOrDispatcher -> require_admin_or_dispatcher
"""

import jwt
from fastapi import Depends, HTTPException, Request, status

from auth.security import decode_token


def get_current_user(request: Request) -> dict:
    header = request.headers.get("authorization")
    if not header or not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = header[7:]
    try:
        return decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_admin_or_dispatcher(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("admin", "dispatcher"):
        raise HTTPException(status_code=403, detail="Admin or dispatcher access required")
    return user
