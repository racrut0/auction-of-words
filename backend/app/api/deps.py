from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ServiceError
from app.core.security import decode_access_token
from app.database import get_session
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None:
        raise ServiceError("Требуется авторизация", status_code=401)

    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise ServiceError("Недействительный токен", status_code=401)

    user = await session.scalar(select(User).where(User.username == username))
    if user is None:
        raise ServiceError("Пользователь не найден", status_code=401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
