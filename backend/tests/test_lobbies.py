import asyncio


async def guest(client, nick):
    response = await client.post("/api/auth/guest", json={"nick": nick})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['token']}"}


async def create_lobby(client, headers, max_players=2, **fields):
    return await client.post(
        "/api/lobbies",
        headers=headers,
        json={
            "settings": {
                "maxPlayers": max_players,
                "startingCoins": 100,
                "rounds": 3,
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
    assert starts[0].json() == starts[1].json()
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
