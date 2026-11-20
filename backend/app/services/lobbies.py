import re
import secrets

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only, selectinload

from app.api.deps import LobbyIdentity
from app.core.errors import ServiceError
from app.models.game import GameStatus
from app.models.lobby import Lobby, LobbyPlayer
from app.models.lobby_auction import LobbyAuctionBid, LobbyAuctionLot
from app.models.lobby_round import LobbyRound, LobbyWordSubmission
from app.schemas.lobby import (
    CreateLobbyRequest, LobbyAuctionDto, LobbyBuildingDto, LobbyPlayerDto, LobbyResultsDto,
    LobbyRoom, LobbySettings, LobbySummary, LotResult,
)
from app.services.lobby_auction import latest_lot
from app.services.lobby_rounds import (
    advance_due, complete_building, current_round, db_now, inventory, restore_round,
    start_round, validate_words,
)
from app.util.word_bank import default_words


CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LIST_LIMIT = 50


def normalize_code(code: str) -> str:
    normalized = code.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6}", normalized):
        raise ServiceError("Код должен содержать 6 латинских букв или цифр", 400)
    return normalized


def player_for(players: list[LobbyPlayer], actor: LobbyIdentity) -> LobbyPlayer | None:
    return next((player for player in players if player.actor_key == actor.key), None)


def require_player(players: list[LobbyPlayer], actor: LobbyIdentity) -> LobbyPlayer:
    player = player_for(players, actor)
    if player is None:
        raise ServiceError("Вы не участник этой партии", 403)
    return player


def require_host(players: list[LobbyPlayer], actor: LobbyIdentity) -> None:
    player = require_player(players, actor)
    if player is not next(member for member in players if member.actor_key is not None):
        raise ServiceError("Это действие доступно только создателю", 403)


def require_waiting(lobby: Lobby) -> None:
    if lobby.status != GameStatus.LOBBY:
        raise ServiceError("Партия уже началась")


def room_view(lobby: Lobby, players: list[LobbyPlayer], actor: LobbyIdentity) -> LobbyRoom:
    member = require_player(players, actor)
    return LobbyRoom(
        id=lobby.id,
        code=lobby.code,
        status=lobby.status,
        current_round=lobby.current_round,
        creator_id=next(p.id for p in players if p.actor_key is not None),
        my_player_id=member.id,
        settings=LobbySettings.model_validate(lobby),
        word_count=len(lobby.words),
        players=[
            LobbyPlayerDto(
                id=p.id, nick=p.nick, ready=p.ready, balance=p.balance,
                turn_position=p.turn_position, left=p.actor_key is None,
            )
            for p in players
        ],
    )


async def locked_room(session: AsyncSession, code: str) -> tuple[Lobby, list[LobbyPlayer]]:
    lobby = await session.scalar(
        select(Lobby).where(Lobby.code == normalize_code(code)).with_for_update()
        .execution_options(populate_existing=True)
    )
    if lobby is None:
        raise ServiceError("Лобби не найдено", 404)
    players = await session.scalars(
        select(LobbyPlayer).where(LobbyPlayer.lobby_id == lobby.id).order_by(LobbyPlayer.id)
        .execution_options(populate_existing=True)
    )
    return lobby, list(players)


async def add_player(session: AsyncSession, lobby: Lobby, actor: LobbyIdentity) -> LobbyPlayer:
    player = await session.scalar(
        insert(LobbyPlayer)
        .values(lobby_id=lobby.id, account_id=actor.account_id, actor_key=actor.key,
                nick=actor.nick, balance=lobby.starting_coins)
        .on_conflict_do_nothing(index_elements=[LobbyPlayer.actor_key])
        .returning(LobbyPlayer)
    )
    if player is None:
        raise ServiceError("Сначала нужно выйти из текущей партии")
    return player


async def list_lobbies(session: AsyncSession, actor: LobbyIdentity) -> list[LobbySummary]:
    own_lobby = (
        select(LobbyPlayer.lobby_id).where(LobbyPlayer.actor_key == actor.key).scalar_subquery()
    )
    is_own = Lobby.id == own_lobby
    result = await session.scalars(
        select(Lobby)
        .where(or_(Lobby.status == GameStatus.LOBBY, is_own))
        .order_by(is_own.desc().nulls_last(), Lobby.id.desc())
        .limit(LIST_LIMIT)
        .options(
            load_only(Lobby.id, Lobby.code, Lobby.status, Lobby.max_players),
            selectinload(Lobby.players).load_only(LobbyPlayer.id, LobbyPlayer.nick, LobbyPlayer.actor_key),
        )
    )
    summaries = []
    for lobby in result:
        active = [player for player in lobby.players if player.actor_key is not None]
        if active:
            summaries.append(LobbySummary(
                code=lobby.code, status=lobby.status, creator_nick=active[0].nick,
                player_count=len(active), max_players=lobby.max_players,
                is_member=player_for(active, actor) is not None,
            ))
    return summaries


async def read_room(session: AsyncSession, actor: LobbyIdentity, code: str) -> LobbyRoom:
    own_player_id = select(LobbyPlayer.id).where(LobbyPlayer.actor_key == actor.key).scalar_subquery()
    latest_lot_id = (
        select(LobbyAuctionLot.id)
        .where(LobbyAuctionLot.lobby_id == Lobby.id, LobbyAuctionLot.round_number == Lobby.current_round)
        .order_by(LobbyAuctionLot.number.desc())
        .limit(1)
        .correlate(Lobby)
        .scalar_subquery()
    )
    rows = await session.execute(
        select(
            Lobby, LobbyRound, LobbyAuctionLot, LobbyAuctionBid.amount,
            LobbyWordSubmission, func.statement_timestamp(),
        )
        .outerjoin(LobbyRound, and_(LobbyRound.lobby_id == Lobby.id, LobbyRound.number == Lobby.current_round))
        .outerjoin(LobbyAuctionLot, and_(Lobby.status == GameStatus.AUCTION, LobbyAuctionLot.id == latest_lot_id))
        .outerjoin(LobbyAuctionBid, and_(
            LobbyAuctionBid.lot_id == LobbyAuctionLot.id, LobbyAuctionBid.player_id == own_player_id,
        ))
        .outerjoin(LobbyWordSubmission, and_(
            Lobby.status == GameStatus.BUILDING, LobbyWordSubmission.lobby_id == Lobby.id,
            LobbyWordSubmission.round_number == Lobby.current_round,
            LobbyWordSubmission.player_id == own_player_id,
        ))
        .where(Lobby.code == normalize_code(code))
        .options(joinedload(Lobby.players))
        .execution_options(populate_existing=True)
    )
    row = rows.unique().one_or_none()
    if row is None:
        raise ServiceError("Лобби не найдено", 404)
    lobby, round_, lot, my_bid, submission, server_time = row
    room = room_view(lobby, lobby.players, actor)

    if round_ is None:
        return room
    if round_.results is not None:
        room.results = LobbyResultsDto(
            **round_.results, ends_at=round_.phase_ends_at, server_time=server_time if round_.phase_ends_at else None
        )
        return room

    closed = select(LobbyAuctionLot).where(
        LobbyAuctionLot.lobby_id == lobby.id, LobbyAuctionLot.round_number == round_.number,
        LobbyAuctionLot.closed_at.is_not(None),
    )
    if lot is not None:
        closed = closed.where(LobbyAuctionLot.number < lot.number)
    closed_lots = await session.scalars(closed.order_by(LobbyAuctionLot.number))
    names = {player.id: player.nick for player in lobby.players}
    history = [
        LotResult(
            number=item.number, letter=item.letter, winner_player_id=item.winner_player_id,
            winner_nick=names.get(item.winner_player_id), winning_amount=item.winning_amount,
        )
        for item in closed_lots
    ]
    letters = [item.letter for item in history if item.winner_player_id == room.my_player_id]
    if lot is not None:
        room.auction = LobbyAuctionDto(
            id=lot.id, number=lot.number, lot_count=len(round_.letters), letter=lot.letter,
            ends_at=lot.ends_at, server_time=server_time, my_bid=my_bid, my_letters=letters, closed_lots=history,
        )
    elif lobby.status == GameStatus.BUILDING:
        room.building = LobbyBuildingDto(
            ends_at=round_.phase_ends_at, server_time=server_time, letters=letters,
            word_bank=lobby.words, submitted_words=submission.words if submission else None, closed_lots=history,
        )
    return room


async def get_room(session: AsyncSession, actor: LobbyIdentity, code: str) -> LobbyRoom:
    room = await read_room(session, actor, code)
    if room.status == GameStatus.AUCTION and room.auction is None:
        lobby, players = await locked_room(session, code)
        require_player(players, actor)
        if lobby.status == GameStatus.AUCTION:
            await restore_round(session, lobby)
        await session.commit()
        return await read_room(session, actor, code)
    return room


async def create_lobby(
    session: AsyncSession, actor: LobbyIdentity, request: CreateLobbyRequest
) -> LobbyRoom:
    for _ in range(8):
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        lobby = await session.scalar(
            insert(Lobby)
            .values(code=code, words=request.words or default_words(), **request.settings.model_dump())
            .on_conflict_do_nothing(index_elements=[Lobby.code])
            .returning(Lobby)
        )
        if lobby is not None:
            player = await add_player(session, lobby, actor)
            await session.commit()
            return room_view(lobby, [player], actor)
    raise ServiceError("Не удалось выдать код. Попробуйте ещё раз", 503)


async def join_lobby(session: AsyncSession, actor: LobbyIdentity, code: str) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    if player_for(players, actor) is None:
        require_waiting(lobby)
        if len(players) >= lobby.max_players:
            raise ServiceError("В этом лобби нет свободных мест")
        players.append(await add_player(session, lobby, actor))
    await session.commit()
    if lobby.status != GameStatus.LOBBY:
        return await get_room(session, actor, code)
    return room_view(lobby, players, actor)


async def set_ready(
    session: AsyncSession, actor: LobbyIdentity, code: str, ready: bool
) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    player = require_player(players, actor)
    require_waiting(lobby)
    player.ready = ready
    await session.commit()
    return room_view(lobby, players, actor)


async def remove_player(
    session: AsyncSession, actor: LobbyIdentity, code: str, player_id: int
) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    require_host(players, actor)
    require_waiting(lobby)
    player = next((p for p in players if p.id == player_id), None)
    if player is None:
        raise ServiceError("Участник не найден", 404)
    if player.actor_key == actor.key:
        raise ServiceError("Создатель не может исключить себя")
    await session.delete(player)
    await session.commit()
    return room_view(lobby, [p for p in players if p is not player], actor)


async def start_game(session: AsyncSession, actor: LobbyIdentity, code: str) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    require_host(players, actor)
    if lobby.status == GameStatus.AUCTION:
        await restore_round(session, lobby)
        await session.commit()
        return await read_room(session, actor, code)
    require_waiting(lobby)
    if len(players) < 2 or any(not p.ready for p in players):
        raise ServiceError("Нужны хотя бы два игрока. Все должны подтвердить готовность")
    order = players.copy()
    if lobby.player_order == "random":
        secrets.SystemRandom().shuffle(order)
    for position, player in enumerate(order, start=1):
        player.turn_position = position
    start_round(session, lobby, 1, await db_now(session))
    await session.commit()
    return await read_room(session, actor, code)


async def submit_bid(
    session: AsyncSession, actor: LobbyIdentity, code: str, lot_id: int, amount: int
) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    player = require_player(players, actor)
    if lobby.status != GameStatus.AUCTION:
        raise ServiceError("Ставку можно сделать во время аукциона")
    lot = await latest_lot(session, lobby)
    round_ = await current_round(session, lobby)
    if lot is None or round_ is None or lot.id != lot_id:
        raise ServiceError("Этот лот уже недоступен")
    now = await db_now(session)
    if lot.closed_at is not None or lot.ends_at <= now:
        if await advance_due(session, lobby, round_, now):
            await session.commit()
        raise ServiceError("Приём ставок завершён")
    if not 1 <= amount <= player.balance:
        raise ServiceError("Ставка должна быть в пределах доступного баланса", 400)

    await session.execute(
        insert(LobbyAuctionBid).values(lot_id=lot.id, player_id=player.id, amount=amount)
        .on_conflict_do_update(index_elements=[LobbyAuctionBid.lot_id, LobbyAuctionBid.player_id],
                               set_={"amount": amount})
    )
    await session.commit()
    return await read_room(session, actor, code)


async def submit_words(
    session: AsyncSession, actor: LobbyIdentity, code: str, round_number: int, words: list[str]
) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    player = require_player(players, actor)
    round_ = await current_round(session, lobby)
    if lobby.status != GameStatus.BUILDING or round_ is None or round_.number != round_number:
        raise ServiceError("Приём слов для этого раунда закрыт")
    now = await db_now(session)
    if now >= round_.phase_ends_at:
        await complete_building(session, lobby, round_, now)
        await session.commit()
        raise ServiceError("Время сборки слов закончилось")
    existing = await session.scalar(select(LobbyWordSubmission.id).where(
        LobbyWordSubmission.lobby_id == lobby.id, LobbyWordSubmission.round_number == round_number,
        LobbyWordSubmission.player_id == player.id,
    ))
    if existing is not None:
        raise ServiceError("Слова уже отправлены")
    letters = await inventory(session, round_)
    normalized = validate_words(words, lobby.words, letters.get(player.id, []))
    session.add(LobbyWordSubmission(
        lobby_id=lobby.id, round_number=round_number, player_id=player.id, words=normalized
    ))
    await complete_building(session, lobby, round_, now)
    await session.commit()
    return await read_room(session, actor, code)


async def next_round(session: AsyncSession, actor: LobbyIdentity, code: str, round_number: int) -> LobbyRoom:
    lobby, players = await locked_room(session, code)
    require_host(players, actor)
    if lobby.status != GameStatus.ROUND_RESULTS or lobby.current_round != round_number:
        raise ServiceError("Этот раунд уже недоступен")
    start_round(session, lobby, round_number + 1, await db_now(session))
    await session.commit()
    return await read_room(session, actor, code)


async def leave_lobby(session: AsyncSession, actor: LobbyIdentity, code: str | None = None) -> None:
    if code is None:
        code = await session.scalar(
            select(Lobby.code).join(LobbyPlayer).where(LobbyPlayer.actor_key == actor.key)
        )
    if code is None:
        return
    try:
        lobby, players = await locked_room(session, code)
    except ServiceError as error:
        if error.status_code != 404:
            raise
        return
    player = player_for(players, actor)
    if player is None:
        return
    if not any(p is not player and p.actor_key is not None for p in players):
        await session.delete(lobby)
    elif lobby.status == GameStatus.LOBBY:
        await session.delete(player)
    else:
        round_ = await current_round(session, lobby)
        now = await db_now(session)
        if round_ is not None and lobby.status in (GameStatus.AUCTION, GameStatus.BUILDING):
            await advance_due(session, lobby, round_, now)
        player.actor_key = None
        if round_ is not None and lobby.status == GameStatus.BUILDING:
            await complete_building(session, lobby, round_, now)
    await session.commit()
