import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ServiceError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.game import Game, GameStatus, PlayerState
from app.models.user import Role, User
from app.schemas.auth import AuthRequest, AuthResponse, ForgotPasswordResponse
from app.schemas.profile import ProfileDto

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RESET_TOKEN_MINUTES = 15


def normalize_email(email: str | None) -> str | None:
    if email is None or not email.strip():
        return None
    return email.strip().lower()


def new_token() -> str:
    return secrets.token_hex(16)


async def _find_by_username(session: AsyncSession, username: str) -> User | None:
    return await session.scalar(select(User).where(User.username == username))


async def _find_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def register(session: AsyncSession, request: AuthRequest) -> AuthResponse:
    username = request.username.strip()
    if await _find_by_username(session, username):
        raise ServiceError("Такое имя уже занято", status_code=409)

    email = normalize_email(request.email)
    if email is not None:
        if not EMAIL_PATTERN.match(email):
            raise ServiceError("Некорректный e-mail", status_code=409)
        if await _find_by_email(session, email):
            raise ServiceError("Этот e-mail уже используется", status_code=409)

    confirmation_token = new_token() if email is not None else None
    user = User(
        username=username,
        email=email,
        email_confirmed=email is None,
        confirmation_token=confirmation_token,
        password=hash_password(request.password),
        role=Role.PLAYER,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(user.id, user.username, user.role.value)
    return AuthResponse(
        token=token,
        username=user.username,
        role=user.role.value,
        email=user.email,
        email_confirmed=user.email_confirmed,
        confirmation_token=confirmation_token,
    )


async def login(session: AsyncSession, request: AuthRequest) -> AuthResponse:
    identifier = request.username.strip()
    user = await _find_by_username(session, identifier)
    if user is None:
        user = await _find_by_email(session, identifier.lower())

    if user is None or not verify_password(request.password, user.password):
        raise ServiceError("Неверное имя/e-mail или пароль", status_code=401)

    token = create_access_token(user.id, user.username, user.role.value)
    return AuthResponse(
        token=token,
        username=user.username,
        role=user.role.value,
        email=user.email,
        email_confirmed=user.email_confirmed,
        confirmation_token=None,
    )


async def confirm_email(session: AsyncSession, token: str | None) -> ForgotPasswordResponse:
    if token is None or not token.strip():
        raise ServiceError("Токен подтверждения не указан", status_code=400)

    user = await session.scalar(select(User).where(User.confirmation_token == token.strip()))
    if user is None:
        raise ServiceError("Ссылка подтверждения недействительна", status_code=400)

    user.email_confirmed = True
    user.confirmation_token = None
    await session.commit()
    return ForgotPasswordResponse(message="E-mail подтверждён", token=None)


async def resend_confirmation(session: AsyncSession, email: str | None) -> ForgotPasswordResponse:
    normalized = normalize_email(email)
    if normalized is None:
        raise ServiceError("Укажите e-mail", status_code=400)

    user = await _find_by_email(session, normalized)
    if user is None:
        raise ServiceError("Пользователь с таким e-mail не найден", status_code=400)

    token = new_token()
    user.confirmation_token = token
    user.email_confirmed = False
    await session.commit()
    return ForgotPasswordResponse(message="Письмо отправлено повторно", token=token)


async def forgot_password(session: AsyncSession, email: str | None) -> ForgotPasswordResponse:
    normalized = normalize_email(email)
    if normalized is None:
        raise ServiceError("Укажите e-mail", status_code=400)

    user = await _find_by_email(session, normalized)
    if user is None:
        return ForgotPasswordResponse(
            message="Если такой e-mail зарегистрирован, ссылка для смены пароля отправлена",
            token=None,
        )

    token = new_token()
    user.reset_token = token
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=RESET_TOKEN_MINUTES
    )
    await session.commit()
    return ForgotPasswordResponse(message="Ссылка для смены пароля сформирована", token=token)


async def reset_password(
    session: AsyncSession, token: str | None, password: str | None
) -> ForgotPasswordResponse:
    if token is None or not token.strip():
        raise ServiceError("Токен смены пароля не указан", status_code=400)
    if password is None or not 4 <= len(password) <= 64:
        raise ServiceError("Пароль должен быть от 4 до 64 символов", status_code=400)

    user = await session.scalar(select(User).where(User.reset_token == token.strip()))
    if user is None:
        raise ServiceError("Ссылка смены пароля недействительна", status_code=400)

    expires_at = user.reset_token_expires_at
    if expires_at is None:
        raise ServiceError("Срок действия ссылки истёк", status_code=400)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise ServiceError("Срок действия ссылки истёк", status_code=400)

    user.password = hash_password(password)
    user.reset_token = None
    user.reset_token_expires_at = None
    await session.commit()
    return ForgotPasswordResponse(message="Пароль изменён", token=None)


async def change_email(session: AsyncSession, user: User, email: str | None) -> ForgotPasswordResponse:
    normalized = normalize_email(email)
    if normalized is None:
        raise ServiceError("Укажите e-mail", status_code=400)
    if not EMAIL_PATTERN.match(normalized):
        raise ServiceError("Некорректный e-mail", status_code=400)

    other = await _find_by_email(session, normalized)
    if other is not None and other.id != user.id:
        raise ServiceError("Этот e-mail уже используется", status_code=400)

    token = new_token()
    user.email = normalized
    user.email_confirmed = False
    user.confirmation_token = token
    await session.commit()
    return ForgotPasswordResponse(message="E-mail изменён, нужно подтверждение", token=token)


async def get_profile(session: AsyncSession, user: User) -> ProfileDto:
    states = (
        await session.scalars(
            select(PlayerState)
            .where(PlayerState.user_id == user.id)
            .order_by(PlayerState.id)
        )
    ).all()

    played = 0
    won = 0
    best = 0
    for state in states:
        game = state.game
        if game is None or game.status != GameStatus.FINISHED:
            continue
        played += 1
        best = max(best, state.score)
        max_score = max((player.score for player in game.players), default=0)
        if state.score >= max_score:
            won += 1

    win_rate = 0.0 if played == 0 else round(100.0 * won / played, 1)
    return ProfileDto(
        username=user.username,
        role=user.role.value,
        email=user.email,
        email_confirmed=user.email_confirmed,
        games_played=played,
        games_won=won,
        win_rate=win_rate,
        best_score=best,
    )
