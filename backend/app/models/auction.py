from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Auction(Base):
    __tablename__ = "auctions"
    __table_args__ = (
        UniqueConstraint(
            "game_id", "round_number", "letter", name="uq_auctions_game_round_letter"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    letter: Mapped[str] = mapped_column(String(1), nullable=False)
    base_price: Mapped[int] = mapped_column(Integer, nullable=False)
    closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    winner_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winning_bid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    game: Mapped["Game"] = relationship(lazy="selectin")
    bids: Mapped[list["AuctionBid"]] = relationship(
        back_populates="auction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AuctionBid(Base):
    __tablename__ = "auction_bids"

    auction_id: Mapped[int] = mapped_column(
        ForeignKey("auctions.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    auction: Mapped[Auction] = relationship(back_populates="bids", lazy="selectin")
