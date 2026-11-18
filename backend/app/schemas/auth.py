from pydantic import Field

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


class ForgotPasswordResponse(CamelModel):
    message: str
    token: str | None


class ConfirmEmailRequest(CamelModel):
    token: str | None = None


class ResetPasswordRequest(CamelModel):
    token: str | None = None
    password: str | None = None
