from fastapi import APIRouter, Depends

from auth.dependencies import get_current_user
from models.auth import LoginRequest, RegisterRequest
from services import auth_service

router = APIRouter()


@router.post("/login", status_code=200)
async def login(body: LoginRequest):
    return auth_service.login(body.email, body.password)


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    return auth_service.register(body.full_name, body.email, body.password, body.role)


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return auth_service.get_me(user["id"])
