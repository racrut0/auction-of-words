from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GameStatus(StrEnum):
    LOBBY = "LOBBY"
    AUCTION = "AUCTION"
    BUILDING = "BUILDING"
    ROUND_RESULTS = "ROUND_RESULTS"
    FINISHED = "FINISHED"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, native_enum=False, length=32),
        default=GameStatus.LOBBY,
        nullable=False,
        index=True,
    )
    current_round: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_rounds: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    max_players: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    starting_capital: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    letter_penalty: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    invite_code: Mapped[str | None] = mapped_column(
        String(8), unique=True, nullable=True, index=True
    )
    turn_order: Mapped[str] = mapped_column(String(16), default="RANDOM", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    build_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    host_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_bank: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    host: Mapped["User"] = relationship(lazy="selectin")
    players: Mapped[list["PlayerState"]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="PlayerState.id",
        lazy="selectin",
    )


class PlayerState(Base):
    __tablename__ = "player_states"
    __table_args__ = (UniqueConstraint("game_id", "user_id", name="uq_player_states_game_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    money: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    words_submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_round_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_round_words: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_round_base_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_round_first_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_round_letter_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_round_money_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_round_words_list: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    total_word_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_first_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_letter_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_money_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    inventory: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    collected_words: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    game: Mapped[Game] = relationship(back_populates="players", lazy="selectin")
    user: Mapped["User"] = relationship(lazy="selectin")


class GameEvent(Base):
    __tablename__ = "game_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    round_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
