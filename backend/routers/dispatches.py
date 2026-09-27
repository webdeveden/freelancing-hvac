from typing import Optional

from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user
from models.dispatches import CreateDispatchRequest, UpdateDispatchStatusRequest
from services import dispatches_service

router = APIRouter()


@router.get("")
async def list_dispatches(
    status: Optional[str] = None,
    tech_id: Optional[int] = None,
    dispatched_by: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    return dispatches_service.list_dispatches(status, tech_id, dispatched_by, page, limit)


@router.get("/{id}")
async def get_dispatch(id: int, user: dict = Depends(get_current_user)):
    return dispatches_service.get_dispatch(id)


@router.post("", status_code=201)
async def create_dispatch(body: CreateDispatchRequest, user: dict = Depends(get_current_user)):
    return await dispatches_service.create_dispatch(user, body.job_id, body.tech_id, body.dispatch_notes)


@router.patch("/{id}/status")
async def update_dispatch_status(id: int, body: UpdateDispatchStatusRequest, user: dict = Depends(get_current_user)):
    return await dispatches_service.update_dispatch_status(id, body.status)
