import re
from typing import Literal

from pydantic import Field, field_validator

from app.models.game import GameStatus
from app.schemas.common import CamelModel


class LobbySettings(CamelModel):
    max_players: int = Field(strict=True, ge=2, le=6)
    starting_coins: int = Field(strict=True, ge=1, le=10000)
    rounds: int = Field(strict=True, ge=1, le=10)
    player_order: Literal["random", "join"]
    letter_penalty: int = Field(strict=True, ge=0, le=100)


class CreateLobbyRequest(CamelModel):
    settings: LobbySettings
    words: list[str] | None = Field(default=None, min_length=1, max_length=1000)

    @field_validator("words")
    @classmethod
    def normalize_words(cls, words: list[str] | None) -> list[str] | None:
        if words is None:
            return None
        normalized = [word.strip().upper().replace("Ё", "Е") for word in words]
        if any(not re.fullmatch(r"[А-Я]{2,30}", word) for word in normalized):
            raise ValueError("Банк должен содержать русские слова длиной от 2 до 30 букв")
        return list(dict.fromkeys(normalized))


class ReadyRequest(CamelModel):
    ready: bool = Field(strict=True)


class LobbySummary(CamelModel):
    code: str
    status: GameStatus
    creator_nick: str
    player_count: int
    max_players: int
    is_member: bool


class LobbyPlayerDto(CamelModel):
    id: int
    nick: str
    ready: bool
    balance: int
    turn_position: int | None
    left: bool


class LobbyRoom(CamelModel):
    id: int
    code: str
    status: GameStatus
    current_round: int
    creator_id: int
    my_player_id: int
    settings: LobbySettings
    word_count: int
    players: list[LobbyPlayerDto]
