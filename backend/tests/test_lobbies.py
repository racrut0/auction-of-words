import asyncio

from sqlalchemy import delete, func, update

from app.config import settings
from app.database import SessionLocal
from app.models.lobby_auction import LobbyAuctionLot
from app.models.lobby_round import LobbyRound
from app.services.lobby_rounds import advance_next_due_round


async def guest(client, nick):
    response = await client.post("/api/auth/guest", json={"nick": nick})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['token']}"}


async def create_lobby(client, headers, max_players=2, rounds=3, **fields):
    return await client.post(
        "/api/lobbies",
        headers=headers,
        json={
            "settings": {
                "maxPlayers": max_players,
                "startingCoins": 100,
                "rounds": rounds,
                "letterPenalty": 2,
                "playerOrder": "join",
            },
            **fields,
        },
    )


async def ready(client, url, headers, value=True):
    return await client.put(f"{url}/ready", headers=headers, json={"ready": value})


async def test_account_and_guest_can_start_one_round(client):
    registered = await client.post("/api/auth/register", json={"username": "host", "password": "secret1"})
    registered.raise_for_status()
    host = {"Authorization": f"Bearer {registered.json()['token']}"}
    player = await guest(client, "Лис")
    outsider = await guest(client, "Кот")
    created = await create_lobby(client, host)
    assert created.status_code == 201
    room = created.json()
    code = room["code"]
    url = f"/api/lobbies/{code}"
    assert room["wordCount"] == 30 and room["currentRound"] == 0
    assert room["myPlayerId"] == room["creatorId"]
    assert (await client.get(url, headers=outsider)).status_code == 403
    assert (await client.get("/api/profile", headers=player)).status_code == 401
    assert (await client.post(f"{url}/start", headers=host)).status_code == 409

    joined = await client.post(f"/api/lobbies/{code.lower()}/join", headers=player)
    repeated = await client.post(f"{url}/join", headers=player)
    assert joined.status_code == 200
    assert repeated.json() == joined.json()
    assert [p["nick"] for p in joined.json()["players"]] == ["host", "Лис"]
    assert (await client.post(f"{url}/start", headers=player)).status_code == 403
    assert (await client.post(f"{url}/start", headers=host)).status_code == 409

    await asyncio.gather(ready(client, url, host), ready(client, url, player))
    starts = await asyncio.gather(
        client.post(f"{url}/start", headers=host),
        client.post(f"{url}/start", headers=host),
    )
    assert all(response.status_code == 200 for response in starts)
    rooms = [response.json() for response in starts]
    for room in rooms:
        room["auction"].pop("serverTime")
    assert rooms[0] == rooms[1]
    current = (await client.get(url, headers=player)).json()
    assert current["status"] == "AUCTION" and current["currentRound"] == 1
    assert [p["turnPosition"] for p in current["players"]] == [1, 2]
    assert all(p["balance"] == 100 for p in current["players"])
    assert (await client.post(f"{url}/join", headers=outsider)).status_code == 409
    assert (await ready(client, url, player, False)).status_code == 409


async def test_one_remaining_seat_cannot_be_taken_twice(client):
    host, first, second = await asyncio.gather(
        guest(client, "Лис"), guest(client, "Кот"), guest(client, "Ёж")
    )
    room = (await create_lobby(client, host)).json()
    url = f"/api/lobbies/{room['code']}"
    replies = await asyncio.gather(*(
        client.post(f"{url}/join", headers=actor) for actor in (first, second)
    ))
    assert sorted(response.status_code for response in replies) == [200, 409]
    assert len((await client.get(url, headers=host)).json()["players"]) == 2


async def test_actor_cannot_create_two_rooms_concurrently(client):
    host = await guest(client, "Лис")
    replies = await asyncio.gather(create_lobby(client, host), create_lobby(client, host))
    assert sorted(response.status_code for response in replies) == [201, 409]
    listed = (await client.get("/api/lobbies", headers=host)).json()
    assert len(listed) == 1 and listed[0]["isMember"]
    assert listed[0]["playerCount"] == 1 and listed[0]["creatorNick"] == "Лис"


async def test_host_can_kick_and_leaving_transfers_host(client):
    host, player, kicked = await asyncio.gather(
        guest(client, "Лис"), guest(client, "Кот"), guest(client, "Ёж")
    )
    room = (await create_lobby(client, host, max_players=3)).json()
    url = f"/api/lobbies/{room['code']}"
    joined = (await client.post(f"{url}/join", headers=player)).json()
    kicked_room = (await client.post(f"{url}/join", headers=kicked)).json()
    kick_url = f"{url}/players/{kicked_room['myPlayerId']}"
    assert (await client.delete(kick_url, headers=player)).status_code == 403
    assert (await client.delete(kick_url, headers=host)).status_code == 200
    assert (await client.get(url, headers=kicked)).status_code == 403
    assert (await client.delete("/api/lobbies/membership", headers=host)).status_code == 200
    updated = (await client.get(url, headers=player)).json()
    assert updated["creatorId"] == joined["myPlayerId"]
    assert (await client.delete(f"{url}/players/me", headers=player)).status_code == 200
    assert (await client.get(url, headers=player)).status_code == 404


async def test_leaving_started_game_keeps_original_player_record(client):
    host, player = await asyncio.gather(guest(client, "Лис"), guest(client, "Кот"))
    room = (await create_lobby(client, host)).json()
    url = f"/api/lobbies/{room['code']}"
    await client.post(f"{url}/join", headers=player)
    await asyncio.gather(ready(client, url, host), ready(client, url, player))
    start = await client.post(f"{url}/start", headers=host)
    start.raise_for_status()
    await client.delete(f"{url}/players/me", headers=player)
    current = (await client.get(url, headers=host)).json()
    assert [p["left"] for p in current["players"]] == [False, True]
    assert (await client.post(f"{url}/join", headers=player)).status_code == 409
    assert (await create_lobby(client, player)).status_code == 201


async def test_validates_guest_bank_and_lobby_code_on_server(client):
    assert (await client.post("/api/auth/guest", json={"nick": " ! "})).status_code == 422
    assert (await client.get("/api/lobbies")).status_code == 401
    host = await guest(client, "Лис")
    assert (await create_lobby(client, host, max_players=7)).status_code == 422
    assert (await create_lobby(client, host, words=[])).status_code == 422
    assert (await create_lobby(client, host, words=["word"])).status_code == 422
    assert (await client.post("/api/lobbies/12/join", headers=host)).status_code == 400
    assert (await client.post("/api/lobbies/000000/join", headers=host)).status_code == 404
    created = await create_lobby(client, host, words=[" ёж ", "ЕЖ", "КОТ"])
    assert created.status_code == 201
    assert created.json()["wordCount"] == 2


async def start_auction(client, **options):
    host, player = await asyncio.gather(guest(client, "Лис"), guest(client, "Кот"))
    created = await create_lobby(client, host, **options)
    created.raise_for_status()
    url = f"/api/lobbies/{created.json()['code']}"
    (await client.post(f"{url}/join", headers=player)).raise_for_status()
    for response in await asyncio.gather(ready(client, url, host), ready(client, url, player)):
        response.raise_for_status()
    started = await client.post(f"{url}/start", headers=host)
    started.raise_for_status()
    return url, host, player, started.json()["auction"]


async def expire_lot(lot_id):
    async with SessionLocal.begin() as session:
        await session.execute(
            update(LobbyAuctionLot).where(LobbyAuctionLot.id == lot_id).values(ends_at=func.clock_timestamp())
        )


async def bid(client, url, headers, lot_id, amount):
    return await client.put(f"{url}/auction/bid", headers=headers, json={"lotId": lot_id, "amount": amount})


async def submit(client, url, headers, words, round_number=1):
    return await client.post(f"{url}/words", headers=headers, json={"roundNumber": round_number, "words": words})


async def expire_stage(room):
    async with SessionLocal.begin() as session:
        await session.execute(update(LobbyRound).where(
            LobbyRound.lobby_id == room["id"], LobbyRound.number == room["currentRound"],
        ).values(phase_ends_at=func.clock_timestamp()))


async def test_auction_keeps_bids_private_and_charges_winner_once(client):
    url, host, player, lot = await start_auction(client)
    assert lot["letter"] == "К" and lot["number"] == 1 and lot["myBid"] is None
    assert lot["lotCount"] == settings.game_letters_per_auction
    outsider = await guest(client, "Ёж")
    assert (await bid(client, url, outsider, lot["id"], 50)).status_code == 403
    assert (await bid(client, url, host, lot["id"], 101)).status_code == 400
    assert (await bid(client, url, host, lot["id"], 0)).status_code == 422

    for amount in (35, 30):
        saved = await bid(client, url, host, lot["id"], amount)
        saved.raise_for_status()
        assert saved.json()["auction"]["myBid"] == amount
    current = (await client.get(url, headers=player)).json()
    assert current["auction"]["myBid"] is None
    saved = (await bid(client, url, player, lot["id"], 40)).json()
    assert saved["auction"]["myBid"] == 40
    assert saved["auction"]["closedLots"] == []
    assert [entry["balance"] for entry in saved["players"]] == [100, 100]

    await expire_lot(lot["id"])
    workers = await asyncio.gather(advance_next_due_round(), advance_next_due_round(), advance_next_due_round())
    assert workers.count(True) == 1
    assert (await bid(client, url, host, lot["id"], 99)).status_code == 409
    for headers, letters in ((host, []), (player, ["К"])):
        current = (await client.get(url, headers=headers)).json()
        result = current["auction"]
        assert result["number"] == 2 and result["myBid"] is None
        previous = result["closedLots"][-1]
        assert previous["winningAmount"] == 40 and previous["winnerNick"] == "Кот"
        assert result["myLetters"] == letters
        assert [entry["balance"] for entry in current["players"]] == [100, 60]


async def test_tied_bids_use_turn_order_and_late_bid_is_rejected(client):
    url, host, player, lot = await start_auction(client)
    for headers in (player, host):
        (await bid(client, url, headers, lot["id"], 20)).raise_for_status()

    await expire_lot(lot["id"])
    assert (await bid(client, url, player, lot["id"], 21)).status_code == 409
    current = (await client.get(url, headers=host)).json()
    assert current["auction"]["closedLots"][0]["winnerNick"] == "Лис"
    assert current["auction"]["closedLots"][0]["winningAmount"] == 20
    assert [entry["balance"] for entry in current["players"]] == [80, 100]


async def test_older_started_room_opens_same_lot_for_both_players(client):
    url, host, player, lot = await start_auction(client)
    async with SessionLocal.begin() as session:
        await session.execute(delete(LobbyRound))
        await session.execute(delete(LobbyAuctionLot).where(LobbyAuctionLot.id == lot["id"]))

    responses = await asyncio.gather(client.get(url, headers=host), client.get(url, headers=player))
    lots = [response.json()["auction"] for response in responses]
    assert lots[0]["id"] == lots[1]["id"] != lot["id"]
    await expire_lot(lots[0]["id"])
    assert await advance_next_due_round()
    result = (await client.get(url, headers=host)).json()
    assert result["auction"]["closedLots"][0]["winnerPlayerId"] is None
    assert [entry["balance"] for entry in result["players"]] == [100, 100]


async def test_round_scores_unique_word_unused_letter_and_final_balance(client, monkeypatch):
    monkeypatch.setattr(settings, "game_letters_per_auction", 4)
    url, host, player, lot = await start_auction(client, words=["КОТ", "КО"], rounds=2)
    for amount in (5, 5, 5, 4):
        (await bid(client, url, host, lot["id"], amount)).raise_for_status()
        await expire_lot(lot["id"])
        assert await advance_next_due_round()
        room = (await client.get(url, headers=host)).json()
        lot = room["auction"]
    assert room["status"] == "BUILDING"
    assert room["building"]["letters"][:3] == ["К", "О", "Т"]
    assert len(room["building"]["closedLots"]) == 4
    assert (await submit(client, url, host, ["ЗАМОК"])).status_code == 400
    assert (await submit(client, url, host, ["КОТ", "КО"])).status_code == 400
    assert (await submit(client, url, host, ["КОТ", "кот"])).status_code == 400
    saved = await submit(client, url, host, [" кот "])
    assert saved.json()["building"]["submittedWords"] == ["КОТ"]
    other = (await client.get(url, headers=player)).json()
    assert other["building"]["submittedWords"] is None
    assert (await submit(client, url, host, [])).status_code == 409

    room = (await submit(client, url, player, [])).json()
    assert room["status"] == "ROUND_RESULTS"
    score = room["results"]["players"][0]
    assert score["words"] == [{"word": "КОТ", "points": 18, "unique": True}]
    assert (score["firstBonus"], score["letterPenalty"], score["roundPoints"], score["totalPoints"]) == (10, 2, 26, 26)
    assert (await client.post(f"{url}/round/next", headers=player, json={"roundNumber": 1})).status_code == 403
    await expire_stage(room)
    assert await advance_next_due_round()
    room = (await client.get(url, headers=host)).json()
    assert room["currentRound"] == 2 and room["auction"]["myLetters"] == []
    assert [entry["balance"] for entry in room["players"]] == [81, 100]
    assert (await client.post(f"{url}/round/next", headers=host, json={"roundNumber": 1})).status_code == 409

    while room["auction"]:
        await expire_lot(room["auction"]["id"])
        assert await advance_next_due_round()
        room = (await client.get(url, headers=host)).json()
    await expire_stage(room)
    assert (await submit(client, url, host, [], round_number=2)).status_code == 409
    room = (await client.get(url, headers=host)).json()
    assert room["status"] == "FINISHED"
    assert room["results"]["winnerIds"] == [room["myPlayerId"]]
    assert [entry["totalPoints"] for entry in room["results"]["players"]] == [66.5, 50]
    assert not await advance_next_due_round()


async def test_shared_word_has_base_score_and_only_first_player_gets_bonus(client, monkeypatch):
    monkeypatch.setattr(settings, "game_letters_per_auction", 6)
    url, host, player, lot = await start_auction(client, words=["КОТ"])
    for bidder in [host] * 3 + [player] * 3:
        (await bid(client, url, bidder, lot["id"], 1)).raise_for_status()
        await expire_lot(lot["id"])
        assert await advance_next_due_round()
        lot = (await client.get(url, headers=host)).json()["auction"]

    (await submit(client, url, player, ["КОТ"])).raise_for_status()
    room = (await submit(client, url, host, ["КОТ"])).json()
    scores = room["results"]["players"]
    assert [entry["nick"] for entry in scores] == ["Кот", "Лис"]
    assert [entry["roundPoints"] for entry in scores] == [19, 9]
    assert all(entry["words"] == [{"word": "КОТ", "points": 9, "unique": False}] for entry in scores)
    room = (await client.post(f"{url}/round/next", headers=host, json={"roundNumber": 1})).json()
    assert room["currentRound"] == 2 and room["auction"]["number"] == 1
