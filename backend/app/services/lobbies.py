import re
import secrets

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only, selectinload

from app.api.deps import LobbyIdentity
from app.core.errors import ServiceError
from app.models.game import GameStatus
from app.models.lobby import Lobby, LobbyPlayer
from app.schemas.lobby import CreateLobbyRequest, LobbyPlayerDto, LobbyRoom, LobbySettings, LobbySummary
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
    )
    if lobby is None:
        raise ServiceError("Лобби не найдено", 404)
    players = await session.scalars(
        select(LobbyPlayer).where(LobbyPlayer.lobby_id == lobby.id).order_by(LobbyPlayer.id)
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


async def get_room(session: AsyncSession, actor: LobbyIdentity, code: str) -> LobbyRoom:
    rows = await session.execute(
        select(Lobby).where(Lobby.code == normalize_code(code)).options(joinedload(Lobby.players))
    )
    lobby = rows.unique().scalar_one_or_none()
    if lobby is None:
        raise ServiceError("Лобби не найдено", 404)
    return room_view(lobby, lobby.players, actor)


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
        await session.commit()
        return room_view(lobby, players, actor)
    require_waiting(lobby)
    if len(players) < 2 or any(not p.ready for p in players):
        raise ServiceError("Нужны хотя бы два игрока. Все должны подтвердить готовность")
    order = players.copy()
    if lobby.player_order == "random":
        secrets.SystemRandom().shuffle(order)
    for position, player in enumerate(order, start=1):
        player.turn_position = position
    lobby.status = GameStatus.AUCTION
    lobby.current_round = 1
    await session.commit()
    return room_view(lobby, players, actor)


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
        player.actor_key = None
    await session.commit()
