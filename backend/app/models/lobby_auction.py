from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LobbyAuctionLot(Base):
    __tablename__ = "lobby_auction_lots"
    __table_args__ = (
        UniqueConstraint("lobby_id", "round_number", "number"),
        Index("ix_lobby_auction_due", "ends_at", postgresql_where=text("closed_at IS NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lobby_id: Mapped[int] = mapped_column(ForeignKey("lobbies.id", ondelete="CASCADE"))
    round_number: Mapped[int]
    number: Mapped[int]
    letter: Mapped[str] = mapped_column(String(1))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    winner_player_id: Mapped[int | None] = mapped_column(
        ForeignKey("lobby_players.id", ondelete="SET NULL")
    )
    winning_amount: Mapped[int | None]


class LobbyAuctionBid(Base):
    __tablename__ = "lobby_auction_bids"

    lot_id: Mapped[int] = mapped_column(ForeignKey("lobby_auction_lots.id", ondelete="CASCADE"), primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("lobby_players.id", ondelete="CASCADE"), primary_key=True)
    amount: Mapped[int]
