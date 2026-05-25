"""
health.py — Health check endpoint

Used by Docker health checks and monitoring to verify the service is running.
"""

from fastapi import APIRouter
from services.call_state import active_count

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "hvac-ai-service",
        "active_calls": active_count(),
    }
