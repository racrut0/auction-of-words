import asyncio
import logging
import random
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import ServiceError
from app.database import SessionLocal
from app.models.game import GameStatus
from app.models.lobby import Lobby, LobbyPlayer
from app.models.lobby_auction import LobbyAuctionLot
from app.models.lobby_round import LobbyRound, LobbyWordSubmission
from app.schemas.lobby import LobbyResultsDto, PlayerRoundResult, ScoredWord
from app.services.lobby_auction import close_lot, latest_lot, open_lot


logger = logging.getLogger(__name__)


def round_letters(words: list[str], first_letter: str | None = None) -> list[str]:
    limit = max(settings.game_letters_per_auction, min(map(len, words)))
    letters = list(first_letter or "")
    candidates = words
    if first_letter:
        candidates = [word.replace(first_letter, "", 1) for word in words]
        limit = max(limit, 1 + min(map(len, candidates)))
    while len(letters) < limit:
        remaining = limit - len(letters)
        fitting = [word for word in candidates if len(word) <= remaining]
        if not fitting:
            letters.extend(random.choices("".join(words), k=remaining))
            break
        letters.extend(fitting[0] if len(letters) <= 1 else random.choice(fitting))
        candidates = words
    return letters


async def db_now(session: AsyncSession) -> datetime:
    return (await session.execute(select(func.clock_timestamp()))).scalar_one()


def start_round(session: AsyncSession, lobby: Lobby, number: int, now: datetime) -> None:
    round_ = LobbyRound(lobby_id=lobby.id, number=number, letters=round_letters(lobby.words))
    session.add(round_)
    lobby.current_round = number
    lobby.status = GameStatus.AUCTION
    open_lot(session, round_, 1, now)


async def current_round(session: AsyncSession, lobby: Lobby) -> LobbyRound | None:
    return await session.get(LobbyRound, (lobby.id, lobby.current_round))


async def restore_round(session: AsyncSession, lobby: Lobby) -> None:
    if await current_round(session, lobby) is not None:
        return
    now = await db_now(session)
    lot = await latest_lot(session, lobby)
    if lot is None:
        start_round(session, lobby, lobby.current_round, now)
        return
    round_ = LobbyRound(lobby_id=lobby.id, number=lobby.current_round, letters=round_letters(lobby.words, lot.letter))
    session.add(round_)
    if lot.closed_at is not None:
        open_lot(session, round_, 2, now)


async def inventory(session: AsyncSession, round_: LobbyRound) -> dict[int, list[str]]:
    lots = await session.scalars(
        select(LobbyAuctionLot)
        .where(
            LobbyAuctionLot.lobby_id == round_.lobby_id,
            LobbyAuctionLot.round_number == round_.number,
            LobbyAuctionLot.winner_player_id.is_not(None),
        )
        .order_by(LobbyAuctionLot.number)
    )
    letters: dict[int, list[str]] = {}
    for lot in lots:
        letters.setdefault(lot.winner_player_id, []).append(lot.letter)
    return letters


def validate_words(words: list[str], bank: list[str], letters: list[str]) -> list[str]:
    normalized = [word.strip().upper().replace("Ё", "Е") for word in words]
    if len(set(normalized)) != len(normalized):
        raise ServiceError("Каждое слово можно выбрать один раз", 400)
    if not set(normalized).issubset(bank):
        raise ServiceError("Можно отправлять только слова из банка", 400)
    if Counter("".join(normalized)) - Counter(letters):
        raise ServiceError("Для выбранных слов не хватает букв", 400)
    return normalized


async def complete_building(
    session: AsyncSession, lobby: Lobby, round_: LobbyRound, now: datetime
) -> bool:
    players = list(await session.scalars(
        select(LobbyPlayer).where(LobbyPlayer.lobby_id == lobby.id).order_by(LobbyPlayer.id)
    ))
    submissions = list(await session.scalars(
        select(LobbyWordSubmission)
        .where(LobbyWordSubmission.lobby_id == lobby.id, LobbyWordSubmission.round_number == round_.number)
        .order_by(LobbyWordSubmission.id)
    ))
    by_player = {submission.player_id: submission.words for submission in submissions}
    if now < round_.phase_ends_at and any(
        player.actor_key is not None and player.id not in by_player for player in players
    ):
        return False

    letters = await inventory(session, round_)
    previous = await session.scalar(
        select(LobbyRound.results).where(LobbyRound.lobby_id == lobby.id, LobbyRound.number == round_.number - 1)
    )
    totals = {entry["player_id"]: entry["total_points"] for entry in previous["players"]} if previous else {}
    counts = Counter(word for submission in submissions for word in submission.words)
    first = next((submission.player_id for submission in submissions if submission.words), None)
    final = round_.number == lobby.rounds
    results = []
    for player in players:
        words = [
            ScoredWord(word=word, points=len(word) ** 2 * (2 if counts[word] == 1 else 1), unique=counts[word] == 1)
            for word in by_player.get(player.id, [])
        ]
        unused = len(letters.get(player.id, [])) - sum(len(word.word) for word in words)
        penalty = unused * lobby.letter_penalty
        first_bonus = 10 if player.id == first else 0
        points = sum(word.points for word in words) + first_bonus - penalty
        coin_bonus = player.balance / 2 if final else 0
        results.append(PlayerRoundResult(
            player_id=player.id, nick=player.nick, words=words, first_bonus=first_bonus,
            unused_letters=unused, letter_penalty=penalty, round_points=points,
            coin_bonus=coin_bonus, total_points=totals.get(player.id, 0) + points + coin_bonus,
        ))

    results.sort(key=lambda entry: -(entry.total_points if final else entry.round_points))
    winner_ids = []
    if final:
        active_ids = {player.id for player in players if player.actor_key is not None}
        eligible = [entry for entry in results if entry.player_id in active_ids]
        if eligible:
            winner_ids = [entry.player_id for entry in eligible if entry.total_points == eligible[0].total_points]
    round_.results = LobbyResultsDto(players=results, winner_ids=winner_ids).model_dump(exclude={"ends_at", "server_time"})
    lobby.status = GameStatus.FINISHED if final else GameStatus.ROUND_RESULTS
    round_.phase_ends_at = None if final else now + timedelta(seconds=settings.game_results_seconds)
    return True


async def advance_due(
    session: AsyncSession, lobby: Lobby, round_: LobbyRound, now: datetime
) -> bool:
    if lobby.status == GameStatus.AUCTION:
        lot = await latest_lot(session, lobby)
        if lot is None or lot.closed_at is not None or now < lot.ends_at:
            return False
        await close_lot(session, lot, now)
        if lot.number < len(round_.letters):
            open_lot(session, round_, lot.number + 1, now)
        else:
            lobby.status = GameStatus.BUILDING
            round_.phase_ends_at = now + timedelta(seconds=settings.game_build_timeout_seconds)
        return True
    if round_.phase_ends_at is None or now < round_.phase_ends_at:
        return False
    if lobby.status == GameStatus.BUILDING:
        return await complete_building(session, lobby, round_, now)
    if lobby.status == GameStatus.ROUND_RESULTS:
        start_round(session, lobby, round_.number + 1, now)
        return True
    return False


async def advance_next_due_round() -> bool:
    async with SessionLocal.begin() as session:
        now = func.statement_timestamp()
        lot_due = exists().where(
            LobbyAuctionLot.lobby_id == Lobby.id,
            LobbyAuctionLot.round_number == Lobby.current_round,
            LobbyAuctionLot.closed_at.is_(None),
            LobbyAuctionLot.ends_at <= now,
        )
        result = await session.execute(
            select(Lobby, LobbyRound)
            .join(LobbyRound, and_(LobbyRound.lobby_id == Lobby.id, LobbyRound.number == Lobby.current_round))
            .where(or_(
                and_(Lobby.status == GameStatus.AUCTION, lot_due),
                and_(
                    Lobby.status.in_([GameStatus.BUILDING, GameStatus.ROUND_RESULTS]),
                    LobbyRound.phase_ends_at <= now,
                ),
            ))
            .order_by(Lobby.id)
            .limit(1)
            .with_for_update(of=Lobby, skip_locked=True)
        )
        row = result.one_or_none()
        if row is None:
            return False
        lobby, round_ = row
        if round_.number != lobby.current_round:
            return False
        await session.refresh(round_)
        return await advance_due(session, lobby, round_, await db_now(session))


async def run_rounds() -> None:
    while True:
        try:
            if await advance_next_due_round():
                continue
        except SQLAlchemyError:
            logger.exception("Failed to advance lobby rounds")
            await asyncio.sleep(4)
        await asyncio.sleep(0.5)
