from app.schemas.common import CamelModel


class ProfileDto(CamelModel):
    username: str
    role: str
    email: str | None
    email_confirmed: bool
    games_played: int
    games_won: int
    win_rate: float
    best_score: int


class ChangeEmailRequest(CamelModel):
    email: str | None = None
