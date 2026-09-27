"""
seed.py — Seed script

Reads JSON mock data from ./seed_data/ and inserts into PostgreSQL.
Handles bcrypt password hashing for users and resolves index-based
references in dispatches (job_index, tech_index, etc.)

Usage:
    python seed.py   (reads credentials from backend/.env)
"""

import json
from pathlib import Path

import psycopg2

from auth.security import hash_password
from config.settings import settings

SEED_DIR = Path(__file__).parent / "seed_data"


def load_json(filename: str):
    return json.loads((SEED_DIR / filename).read_text())


def log(msg: str):
    print(f"[seed] {msg}")


def get_connection():
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


def seed_users(cur) -> list[int]:
    log("Seeding users...")
    users = load_json("users.json")
    inserted_ids = []

    for user in users:
        password_hash = hash_password(user["password"])
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role, full_name, phone)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                role          = EXCLUDED.role,
                full_name     = EXCLUDED.full_name,
                phone         = EXCLUDED.phone
            RETURNING id
            """,
            (user["email"], password_hash, user["role"], user["full_name"], user.get("phone")),
        )
        user_id = cur.fetchone()[0]
        inserted_ids.append(user_id)
        log(f'  → User "{user["full_name"]}" ({user["role"]}) id={user_id}')

    return inserted_ids


def seed_jobs(cur, user_ids: list[int]) -> list[int]:
    log("Seeding jobs...")
    jobs = load_json("jobs.json")
    tech_ids = user_ids[3:]  # indices 3-5 are technicians
    inserted_ids = []

    for i, job in enumerate(jobs):
        tech_id = None
        if job["status"] in ("assigned", "in-progress", "completed"):
            tech_id = tech_ids[i % len(tech_ids)]

        cur.execute(
            """
            INSERT INTO jobs
                (caller_name, caller_phone, service_type, description, address, city,
                 status, priority, assigned_tech_id, scheduled_at, notes, call_sid)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                job["caller_name"], job["caller_phone"], job["service_type"], job["description"],
                job["address"], job["city"], job["status"], job["priority"],
                tech_id, job.get("scheduled_at"), job.get("notes"), job.get("call_sid"),
            ),
        )
        job_id = cur.fetchone()[0]
        inserted_ids.append(job_id)
        log(f'  → Job #{job_id} "{job["service_type"]}" [{job["priority"]}/{job["status"]}]')

    return inserted_ids


def seed_dispatches(cur, job_ids: list[int], user_ids: list[int]):
    log("Seeding dispatches...")
    dispatches = load_json("dispatches.json")
    tech_ids = user_ids[3:]

    for d in dispatches:
        job_id = job_ids[d["job_index"]] if d["job_index"] < len(job_ids) else None
        tech_id = tech_ids[d["tech_index"] - 3] if 0 <= d["tech_index"] - 3 < len(tech_ids) else tech_ids[0]
        dispatched_by_id = user_ids[d["dispatched_by_index"]]

        if not job_id:
            log(f'  ! Skipping dispatch — job_index {d["job_index"]} out of range')
            continue

        cur.execute(
            """
            INSERT INTO dispatches (job_id, tech_id, dispatched_by, dispatch_notes, status)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (job_id, tech_id, dispatched_by_id, d.get("dispatch_notes"), d["status"]),
        )
        log(f'  → Dispatch job #{job_id} → tech #{tech_id} [{d["status"]}]')


def seed_faq(cur):
    log("Seeding FAQ entries...")
    faqs = load_json("faq_entries.json")

    for faq in faqs:
        cur.execute(
            """
            INSERT INTO faq_entries (category, question, answer, keywords)
            VALUES (%s, %s, %s, %s)
            """,
            (faq["category"], faq["question"], faq["answer"], faq["keywords"]),
        )
        log(f'  → FAQ [{faq["category"]}] "{faq["question"][:50]}..."')


def seed_comments(cur, job_ids: list[int], user_ids: list[int]):
    log("Seeding sample comments...")
    admin_id = user_ids[0]
    dispatcher_id = user_ids[1]

    comments = [
        {"job_idx": 1, "author_id": admin_id, "content": "**Emergency flagged** — caller confirmed no heat for 6+ hours. Family with infant. Bumped to top of queue."},
        {"job_idx": 1, "author_id": dispatcher_id, "content": "Called Mike at 8:15 AM. ETA 45 minutes. Client notified via text."},
        {"job_idx": 4, "author_id": dispatcher_id, "content": "**Note:** Derek reports burning smell from wiring harness. May need full motor replacement. Will update with parts estimate."},
        {"job_idx": 4, "author_id": admin_id, "content": "Approved up to $800 for repairs without additional authorization. Call if it exceeds that."},
        {"job_idx": 2, "author_id": dispatcher_id, "content": "Carlos is a service plan member — no charge for this visit. Mark the plan contract number: `SVC-2024-0882`."},
        {"job_idx": 8, "author_id": admin_id, "content": "Install completed on schedule.\n\n- Equipment: Carrier 5-ton split system\n- Permit: pulled and approved\n- Warranty registered: **10-year parts, 5-year labor**"},
    ]

    for c in comments:
        if c["job_idx"] >= len(job_ids):
            continue
        job_id = job_ids[c["job_idx"]]
        cur.execute(
            "INSERT INTO job_comments (job_id, author_id, content) VALUES (%s,%s,%s)",
            (job_id, c["author_id"], c["content"]),
        )
        log(f'  → Comment on job #{job_id} by user #{c["author_id"]}')


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            log("Starting seed transaction...")

            cur.execute("DELETE FROM job_comments")
            cur.execute("DELETE FROM dispatches")
            cur.execute("DELETE FROM jobs")
            cur.execute("DELETE FROM faq_entries")
            cur.execute("DELETE FROM users")
            log("Cleared existing seed data.")

            user_ids = seed_users(cur)
            job_ids = seed_jobs(cur, user_ids)
            seed_dispatches(cur, job_ids, user_ids)
            seed_faq(cur)
            seed_comments(cur, job_ids, user_ids)

        conn.commit()
        log("✓ Seed completed successfully.")
    except Exception as e:
        conn.rollback()
        log(f"ERROR — rolled back: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
