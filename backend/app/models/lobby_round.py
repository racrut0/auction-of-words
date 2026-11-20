from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LobbyRound(Base):
    __tablename__ = "lobby_rounds"

    lobby_id: Mapped[int] = mapped_column(ForeignKey("lobbies.id", ondelete="CASCADE"), primary_key=True)
    number: Mapped[int] = mapped_column(primary_key=True)
    letters: Mapped[list[str]] = mapped_column(JSON)
    phase_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    results: Mapped[dict | None] = mapped_column(JSON)


class LobbyWordSubmission(Base):
    __tablename__ = "lobby_word_submissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["lobby_id", "round_number"], ["lobby_rounds.lobby_id", "lobby_rounds.number"], ondelete="CASCADE"
        ),
        UniqueConstraint("lobby_id", "round_number", "player_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lobby_id: Mapped[int]
    round_number: Mapped[int]
    player_id: Mapped[int] = mapped_column(ForeignKey("lobby_players.id", ondelete="CASCADE"))
    words: Mapped[list[str]] = mapped_column(JSON)
