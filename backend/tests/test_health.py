async def test_health(client):
    response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_root(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/api/health"
