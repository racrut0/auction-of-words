from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.game import GameStatus


class Lobby(Base):
    __tablename__ = "lobbies"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(6), unique=True)
    status: Mapped[str] = mapped_column(String(32), default=GameStatus.LOBBY, index=True)
    current_round: Mapped[int] = mapped_column(default=0)
    max_players: Mapped[int]
    starting_coins: Mapped[int]
    rounds: Mapped[int]
    player_order: Mapped[str] = mapped_column(String(8))
    letter_penalty: Mapped[int]
    words: Mapped[list[str]] = mapped_column(JSON)

    players: Mapped[list["LobbyPlayer"]] = relationship(
        lazy="raise", order_by="LobbyPlayer.id", passive_deletes=True
    )


class LobbyPlayer(Base):
    __tablename__ = "lobby_players"
    __table_args__ = (UniqueConstraint("actor_key", name="uq_lobby_players_actor"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lobby_id: Mapped[int] = mapped_column(ForeignKey("lobbies.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actor_key: Mapped[str | None] = mapped_column(String(48))
    nick: Mapped[str] = mapped_column(String(32))
    ready: Mapped[bool] = mapped_column(default=False)
    balance: Mapped[int]
    turn_position: Mapped[int | None]
