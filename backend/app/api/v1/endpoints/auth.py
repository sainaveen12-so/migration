from fastapi import APIRouter, HTTPException, Request, status

from app.core.deps import DBSession
from app.repositories.job_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.ai_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DBSession):
    auth_svc = AuthService(UserRepository(db), AuditRepository(db))
    try:
        return await auth_svc.register(data.email, data.username, data.password, data.full_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: DBSession):
    auth_svc = AuthService(UserRepository(db), AuditRepository(db))
    try:
        result = await auth_svc.login(data.email, data.password)
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: DBSession):
    auth_svc = AuthService(UserRepository(db))
    try:
        return await auth_svc.refresh_token(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: DBSession):
    auth_svc = AuthService(UserRepository(db))
    try:
        token = await auth_svc.forgot_password(data.email)
        return MessageResponse(
            message="If the email exists, a password reset link has been sent.",
            detail={"reset_token": token} if token else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: DBSession):
    auth_svc = AuthService(UserRepository(db), AuditRepository(db))
    try:
        await auth_svc.reset_password(data.token, data.new_password)
        return MessageResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
