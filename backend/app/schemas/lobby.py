import re
from datetime import datetime
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


class BidRequest(CamelModel):
    lot_id: int = Field(strict=True, ge=1)
    amount: int = Field(strict=True, ge=1)


class RoundRequest(CamelModel):
    round_number: int = Field(strict=True, ge=1)


class SubmitWordsRequest(RoundRequest):
    words: list[str] = Field(max_length=30)


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


class LotResult(CamelModel):
    number: int
    letter: str
    winner_player_id: int | None
    winner_nick: str | None
    winning_amount: int | None


class LobbyAuctionDto(CamelModel):
    id: int
    number: int
    lot_count: int
    letter: str
    ends_at: datetime
    server_time: datetime
    my_bid: int | None
    my_letters: list[str]
    closed_lots: list[LotResult]


class LobbyBuildingDto(CamelModel):
    ends_at: datetime
    server_time: datetime
    letters: list[str]
    word_bank: list[str]
    submitted_words: list[str] | None
    closed_lots: list[LotResult]


class ScoredWord(CamelModel):
    word: str
    points: int
    unique: bool


class PlayerRoundResult(CamelModel):
    player_id: int
    nick: str
    words: list[ScoredWord]
    first_bonus: int
    unused_letters: int
    letter_penalty: int
    round_points: int
    coin_bonus: float
    total_points: float


class LobbyResultsDto(CamelModel):
    players: list[PlayerRoundResult]
    winner_ids: list[int]
    ends_at: datetime | None = None
    server_time: datetime | None = None


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
    auction: LobbyAuctionDto | None = None
    building: LobbyBuildingDto | None = None
    results: LobbyResultsDto | None = None
