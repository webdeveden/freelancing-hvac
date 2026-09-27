from typing import Optional

from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user, require_admin
from models.faq import CreateFAQRequest, UpdateFAQRequest
from services import faq_service

router = APIRouter()


@router.get("")
async def list_faq(category: Optional[str] = None, active: Optional[bool] = None, user: dict = Depends(get_current_user)):
    return faq_service.list_faq(category, active)


@router.post("", status_code=201)
async def create_faq_entry(body: CreateFAQRequest, user: dict = Depends(require_admin)):
    return faq_service.create_faq_entry(body.category, body.question, body.answer, body.keywords)


@router.patch("/{id}")
async def update_faq_entry(id: int, body: UpdateFAQRequest, user: dict = Depends(require_admin)):
    return faq_service.update_faq_entry(id, body.category, body.question, body.answer, body.keywords, body.active)


@router.delete("/{id}")
async def delete_faq_entry(id: int, user: dict = Depends(require_admin)):
    return faq_service.delete_faq_entry(id)
