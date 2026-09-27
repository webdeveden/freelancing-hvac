from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user
from services import techs_service

router = APIRouter()


@router.get("")
async def list_techs(user: dict = Depends(get_current_user)):
    return techs_service.list_techs()
