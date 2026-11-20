from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ServiceError
from app.core.security import decode_access_token
from app.database import get_session
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class LobbyIdentity:
    key: str
    nick: str
    account_id: int | None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None:
        raise ServiceError("Требуется авторизация", status_code=401)

    payload = decode_access_token(credentials.credentials)
    if payload.get("role") == "GUEST":
        raise ServiceError("Требуется аккаунт", status_code=401)
    username = payload.get("sub")
    if not username:
        raise ServiceError("Недействительный токен", status_code=401)

    user = await session.scalar(select(User).where(User.username == username))
    if user is None:
        raise ServiceError("Пользователь не найден", status_code=401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


async def get_lobby_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: DbSession,
) -> LobbyIdentity:
    if credentials is None:
        raise ServiceError("Требуется авторизация", status_code=401)
    payload = decode_access_token(credentials.credentials)
    if payload.get("role") == "GUEST":
        nick = payload.get("nick")
        subject = payload.get("sub")
        if isinstance(nick, str) and isinstance(subject, str):
            try:
                return LobbyIdentity(f"guest:{UUID(subject)}", nick, None)
            except ValueError:
                pass
        raise ServiceError("Недействительная гостевая сессия", status_code=401)

    account_id = payload.get("uid")
    user = await session.get(User, account_id) if type(account_id) is int else None
    if user is None:
        raise ServiceError("Пользователь не найден", status_code=401)
    return LobbyIdentity(f"account:{user.id}", user.username, user.id)


LobbyActor = Annotated[LobbyIdentity, Depends(get_lobby_identity)]
