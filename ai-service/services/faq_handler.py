"""
faq_handler.py — FAQ retrieval from PostgreSQL

Queries the faq_entries table for relevant answers using keyword overlap.
Results are injected into the AI context when a caller asks a general question,
preventing the AI from hallucinating prices, hours, or availability.
"""

import psycopg2
import psycopg2.extras
from config.settings import settings


def get_connection():
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


def get_relevant_faqs(speech_text: str, limit: int = 3) -> list[dict]:
    """
    Returns up to `limit` FAQ entries whose keywords overlap with the caller's speech.
    Uses PostgreSQL's array overlap operator (&&) for efficient keyword matching.
    Falls back to a full active FAQ list if no keyword match is found.
    """
    # Extract simple lowercase words from speech for keyword matching
    words = [w.strip(".,!?") for w in speech_text.lower().split() if len(w) > 3]
    if not words:
        return []

    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Try keyword overlap first
            cur.execute(
                """
                SELECT category, question, answer
                FROM faq_entries
                WHERE active = TRUE AND keywords && %s
                LIMIT %s
                """,
                (words, limit)
            )
            rows = cur.fetchall()

            # Fallback: return top FAQ entries if no keyword match
            if not rows:
                cur.execute(
                    "SELECT category, question, answer FROM faq_entries WHERE active = TRUE LIMIT %s",
                    (limit,)
                )
                rows = cur.fetchall()

        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[faq_handler] DB error: {e}")
        return []


def format_faqs_for_prompt(faqs: list[dict]) -> str:
    """Returns a compact text block to inject into the AI system prompt."""
    if not faqs:
        return ""
    lines = ["RELEVANT FAQ CONTEXT:"]
    for faq in faqs:
        lines.append(f"Q: {faq['question']}")
        lines.append(f"A: {faq['answer']}")
        lines.append("")
    return "\n".join(lines)
