from typing import Optional

from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user, require_admin, require_admin_or_dispatcher
from models.jobs import AddCommentRequest, AssignTechRequest, CreateJobRequest, UpdateJobRequest
from services import jobs_service

router = APIRouter()


@router.get("")
async def list_jobs(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_tech_id: Optional[int] = None,
    source: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    return jobs_service.list_jobs(user, status, priority, assigned_tech_id, source, page, limit)


@router.get("/{id}")
async def get_job(id: int, user: dict = Depends(get_current_user)):
    return jobs_service.get_job(id)


@router.post("", status_code=201)
async def create_job(body: CreateJobRequest, user: dict = Depends(require_admin)):
    return await jobs_service.create_job(body)


@router.patch("/{id}")
async def update_job(id: int, body: UpdateJobRequest, user: dict = Depends(get_current_user)):
    return await jobs_service.update_job(user, id, body)


@router.patch("/{id}/assign")
async def assign_tech(id: int, body: AssignTechRequest, user: dict = Depends(require_admin)):
    return await jobs_service.assign_tech(user, id, body.tech_id)


@router.patch("/{id}/unassign")
async def unassign_tech(id: int, user: dict = Depends(require_admin_or_dispatcher)):
    return await jobs_service.unassign_tech(id)


@router.post("/{id}/claim")
async def claim_job(id: int, user: dict = Depends(get_current_user)):
    return await jobs_service.claim_job(user, id)


@router.patch("/{id}/approve")
async def approve_request(id: int, user: dict = Depends(require_admin_or_dispatcher)):
    return await jobs_service.approve_request(user, id)


@router.patch("/{id}/reject")
async def reject_request(id: int, user: dict = Depends(require_admin_or_dispatcher)):
    return await jobs_service.reject_request(id)


@router.delete("/{id}")
async def delete_job(id: int, user: dict = Depends(require_admin)):
    return await jobs_service.delete_job(id)


@router.get("/{id}/comments")
async def get_comments(id: int, user: dict = Depends(get_current_user)):
    return jobs_service.get_comments(id)


@router.post("/{id}/comments", status_code=201)
async def add_comment(id: int, body: AddCommentRequest, user: dict = Depends(get_current_user)):
    return await jobs_service.add_comment(user, id, body.content)


@router.delete("/{id}/comments/{cid}")
async def delete_comment(id: int, cid: int, user: dict = Depends(get_current_user)):
    return await jobs_service.delete_comment(user, id, cid)
