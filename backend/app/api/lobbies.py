from fastapi import APIRouter

from app.api.deps import DbSession, LobbyActor
from app.schemas.lobby import (
    BidRequest, CreateLobbyRequest, LobbyRoom, LobbySummary, ReadyRequest, RoundRequest, SubmitWordsRequest,
)
from app.services import lobbies


router = APIRouter(prefix="/lobbies", tags=["lobbies"])


@router.get("")
async def list_lobbies(session: DbSession, actor: LobbyActor) -> list[LobbySummary]:
    return await lobbies.list_lobbies(session, actor)


@router.post("", status_code=201)
async def create_lobby(request: CreateLobbyRequest, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.create_lobby(session, actor, request)


@router.get("/{code}")
async def lobby_room(code: str, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.get_room(session, actor, code)


@router.post("/{code}/join")
async def join_lobby(code: str, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.join_lobby(session, actor, code)


@router.put("/{code}/ready")
async def set_ready(code: str, request: ReadyRequest, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.set_ready(session, actor, code, request.ready)


@router.post("/{code}/start")
async def start_game(code: str, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.start_game(session, actor, code)


@router.put("/{code}/auction/bid")
async def submit_bid(code: str, request: BidRequest, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.submit_bid(session, actor, code, request.lot_id, request.amount)


@router.post("/{code}/words")
async def submit_words(code: str, request: SubmitWordsRequest, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.submit_words(session, actor, code, request.round_number, request.words)


@router.post("/{code}/round/next")
async def next_round(code: str, request: RoundRequest, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.next_round(session, actor, code, request.round_number)


@router.delete("/membership")
async def leave_current_lobby(session: DbSession, actor: LobbyActor) -> dict[str, bool]:
    await lobbies.leave_lobby(session, actor)
    return {"ok": True}


@router.delete("/{code}/players/me")
async def leave_lobby(code: str, session: DbSession, actor: LobbyActor) -> dict[str, bool]:
    await lobbies.leave_lobby(session, actor, code)
    return {"ok": True}


@router.delete("/{code}/players/{player_id}")
async def remove_player(code: str, player_id: int, session: DbSession, actor: LobbyActor) -> LobbyRoom:
    return await lobbies.remove_player(session, actor, code, player_id)
