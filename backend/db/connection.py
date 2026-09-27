"""
connection.py — PostgreSQL connection helper

Mirrors the ai-service pattern (ai-service/services/job_creator.py):
synchronous psycopg2, a new connection per operation, closed in `finally`.
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
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
