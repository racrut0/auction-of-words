from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import ForgotPasswordResponse
from app.schemas.profile import ChangeEmailRequest, ProfileDto
from app.services import auth as auth_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileDto)
async def profile(user: CurrentUser, session: DbSession) -> ProfileDto:
    return await auth_service.get_profile(session, user)


@router.put("/email", response_model=ForgotPasswordResponse)
async def change_email(
    request: ChangeEmailRequest, user: CurrentUser, session: DbSession
) -> ForgotPasswordResponse:
    return await auth_service.change_email(session, user, request.email)
