from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lobby import Lobby, LobbyPlayer
from app.models.lobby_auction import LobbyAuctionBid, LobbyAuctionLot
from app.models.lobby_round import LobbyRound


async def latest_lot(session: AsyncSession, lobby: Lobby) -> LobbyAuctionLot | None:
    return await session.scalar(
        select(LobbyAuctionLot)
        .where(LobbyAuctionLot.lobby_id == lobby.id, LobbyAuctionLot.round_number == lobby.current_round)
        .order_by(LobbyAuctionLot.number.desc())
        .limit(1)
    )


def open_lot(session: AsyncSession, round_: LobbyRound, number: int, now: datetime) -> None:
    session.add(LobbyAuctionLot(
        lobby_id=round_.lobby_id,
        round_number=round_.number,
        number=number,
        letter=round_.letters[number - 1],
        ends_at=now + timedelta(seconds=settings.game_auction_seconds),
    ))


async def close_lot(session: AsyncSession, lot: LobbyAuctionLot, now: datetime) -> None:
    result = await session.execute(
        select(LobbyPlayer, LobbyAuctionBid.amount)
        .join(LobbyAuctionBid, LobbyAuctionBid.player_id == LobbyPlayer.id)
        .where(LobbyAuctionBid.lot_id == lot.id, LobbyPlayer.actor_key.is_not(None))
        .order_by(LobbyAuctionBid.amount.desc(), LobbyPlayer.turn_position.asc().nulls_last(), LobbyPlayer.id)
        .limit(1)
    )
    winner = result.one_or_none()
    if winner is not None:
        player, amount = winner
        player.balance -= amount
        lot.winner_player_id = player.id
        lot.winning_amount = amount
    lot.closed_at = now
