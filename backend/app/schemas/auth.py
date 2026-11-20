from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import CamelModel


class AuthRequest(CamelModel):
    username: str = Field(min_length=3, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    password: str = Field(min_length=4, max_length=64)


class AuthResponse(CamelModel):
    token: str
    username: str
    role: str
    email: str | None
    email_confirmed: bool
    confirmation_token: str | None


class ForgotPasswordRequest(CamelModel):
    email: str | None = None


class GuestRequest(CamelModel):
    nick: str = Field(max_length=20)

    @field_validator("nick")
    @classmethod
    def validate_nick(cls, value: str) -> str:
        nick = value.strip()
        if len(nick) < 2 or not all(char.isalnum() or char in " _-" for char in nick):
            raise ValueError("Допустимы буквы, цифры, пробел, подчёркивание и дефис")
        return nick


class GuestResponse(CamelModel):
    username: str
    token: str
    guest: Literal[True] = True


class ForgotPasswordResponse(CamelModel):
    message: str
    token: str | None


class ConfirmEmailRequest(CamelModel):
    token: str | None = None


class ResetPasswordRequest(CamelModel):
    token: str | None = None
    password: str | None = None
