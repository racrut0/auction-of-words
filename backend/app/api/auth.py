from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.auth import (
    AuthRequest,
    AuthResponse,
    ConfirmEmailRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(request: AuthRequest, session: DbSession) -> AuthResponse:
    return await auth_service.register(session, request)


@router.post("/login", response_model=AuthResponse)
async def login(request: AuthRequest, session: DbSession) -> AuthResponse:
    return await auth_service.login(session, request)


@router.post("/confirm-email", response_model=ForgotPasswordResponse)
async def confirm_email(
    request: ConfirmEmailRequest, session: DbSession
) -> ForgotPasswordResponse:
    return await auth_service.confirm_email(session, request.token)


@router.post("/resend-confirmation", response_model=ForgotPasswordResponse)
async def resend_confirmation(
    request: ForgotPasswordRequest, session: DbSession
) -> ForgotPasswordResponse:
    return await auth_service.resend_confirmation(session, request.email)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest, session: DbSession
) -> ForgotPasswordResponse:
    return await auth_service.forgot_password(session, request.email)


@router.post("/reset-password", response_model=ForgotPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest, session: DbSession
) -> ForgotPasswordResponse:
    return await auth_service.reset_password(session, request.token, request.password)
