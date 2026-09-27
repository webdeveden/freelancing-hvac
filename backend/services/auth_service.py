from fastapi import HTTPException

from auth.security import create_token, hash_password, verify_password
from db.connection import get_connection


def login(email: str | None, password: str | None) -> dict:
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, role, full_name
                FROM users
                WHERE email = %s AND is_active = true
                """,
                (email.strip().lower(),),
            )
            user = cur.fetchone()
    finally:
        conn.close()

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(id=user["id"], email=user["email"], role=user["role"], name=user["full_name"])
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "role": user["role"], "name": user["full_name"]},
    }


def register(full_name: str | None, email: str | None, password: str | None, role: str | None) -> dict:
    if not full_name or not email or not password:
        raise HTTPException(status_code=400, detail="full_name, email, and password are required")

    user_role = role if role in ("dispatcher", "tech") else "dispatcher"
    normalized_email = email.strip().lower()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (normalized_email,))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="An account with that email already exists")

            password_hash = hash_password(password)
            cur.execute(
                """
                INSERT INTO users (full_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, role, full_name
                """,
                (full_name.strip(), normalized_email, password_hash, user_role),
            )
            user = cur.fetchone()
        conn.commit()
    finally:
        conn.close()

    token = create_token(id=user["id"], email=user["email"], role=user["role"], name=user["full_name"])
    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "role": user["role"], "name": user["full_name"]},
    }


def get_me(user_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, role, full_name, phone FROM users WHERE id = %s",
                (user_id,),
            )
            user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}
