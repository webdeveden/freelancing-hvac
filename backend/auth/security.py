"""
security.py — Password hashing and JWT encode/decode helpers

bcrypt hashes here are wire-compatible with the previous Node bcryptjs
hashes (both are standard bcrypt), and PyJWT with HS256 matches the
token format `jsonwebtoken` (Node) produces.
"""

import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config.settings import settings

_DURATION_RE = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_duration_to_timedelta(value: str) -> timedelta:
    """Parses strings like '8h', '30m', '7d' (same shorthand `jsonwebtoken` accepts)."""
    match = _DURATION_RE.match(value.strip())
    if not match:
        return timedelta(hours=8)
    amount, unit = match.groups()
    return timedelta(seconds=int(amount) * _UNIT_SECONDS[unit.lower()])


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(*, id: int, email: str, role: str, name: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "id": id,
        "email": email,
        "role": role,
        "name": name,
        "iat": now,
        "exp": now + _parse_duration_to_timedelta(settings.jwt_expires_in),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError (ExpiredSignatureError / InvalidTokenError) on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
