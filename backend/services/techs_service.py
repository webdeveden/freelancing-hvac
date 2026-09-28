from db.connection import get_connection


def list_techs() -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, full_name, email, phone
                FROM users
                WHERE role = 'tech' AND is_active = true
                ORDER BY full_name ASC
                """
            )
            techs = cur.fetchall()
    finally:
        conn.close()

    return {"techs": techs}
