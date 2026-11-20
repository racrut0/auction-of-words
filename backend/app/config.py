from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Word Auction API"
    debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5433/wordauction"
    )

    jwt_secret: str = "change-me-in-production-very-long-secret-key-please-1234567890"
    jwt_expiration_minutes: int = 1440
    jwt_algorithm: str = "HS256"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    game_starting_capital: int = 100
    game_rounds: int = 3
    game_letters_per_auction: int = Field(default=16, ge=2, le=60)
    game_auction_seconds: int = Field(default=10, ge=1)
    game_build_timeout_seconds: int = Field(default=40, ge=1)
    game_results_seconds: int = Field(default=15, ge=1)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
