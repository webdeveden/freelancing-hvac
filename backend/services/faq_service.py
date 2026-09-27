from fastapi import HTTPException

from db.connection import get_connection


def list_faq(category, active) -> dict:
    conditions, params = [], []
    if category:
        conditions.append("category = %s")
        params.append(category)
    if active is not None:
        conditions.append("active = %s")
        params.append(active)

    where_sql = " AND ".join(conditions) if conditions else "TRUE"

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT * FROM faq_entries WHERE {where_sql} ORDER BY category ASC, id ASC",
                params,
            )
            faq = cur.fetchall()
    finally:
        conn.close()

    return {"faq": faq}


def create_faq_entry(category, question, answer, keywords) -> dict:
    if not question or not answer:
        raise HTTPException(status_code=400, detail="question and answer are required")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO faq_entries (category, question, answer, keywords)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (category or "general", question, answer, keywords or []),
            )
            entry = cur.fetchone()
            conn.commit()
    finally:
        conn.close()

    return {"entry": entry}


def update_faq_entry(entry_id: int, category, question, answer, keywords, active) -> dict:
    data = {}
    if category is not None:
        data["category"] = category
    if question is not None:
        data["question"] = question
    if answer is not None:
        data["answer"] = answer
    if keywords is not None:
        data["keywords"] = keywords
    if active is not None:
        data["active"] = active

    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            set_clause = ", ".join(f"{key} = %s" for key in data)
            cur.execute(
                f"UPDATE faq_entries SET {set_clause}, updated_at = now() WHERE id = %s RETURNING *",
                (*data.values(), entry_id),
            )
            entry = cur.fetchone()
            conn.commit()
    finally:
        conn.close()

    if not entry:
        raise HTTPException(status_code=404, detail="FAQ entry not found")
    return {"entry": entry}


def delete_faq_entry(entry_id: int) -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM faq_entries WHERE id = %s RETURNING id", (entry_id,))
            deleted = cur.fetchone()
            conn.commit()
    finally:
        conn.close()

    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ entry not found")
    return {"message": "FAQ entry deleted", "id": entry_id}
