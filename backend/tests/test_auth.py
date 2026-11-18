import pytest

DEFAULT_PASSWORD = "demo1234"


async def register(
    client,
    username: str = "alice",
    email: str | None = "alice@example.com",
    password: str = DEFAULT_PASSWORD,
):
    return await client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )


async def auth_headers(client, username: str = "alice", password: str = DEFAULT_PASSWORD):
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


async def test_register_returns_token_and_requires_email_confirmation(client):
    response = await register(client)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "alice"
    assert body["role"] == "PLAYER"
    assert body["email"] == "alice@example.com"
    assert body["emailConfirmed"] is False
    assert body["confirmationToken"]
    assert body["token"]


async def test_register_without_email_is_confirmed(client):
    response = await register(client, email=None)

    body = response.json()
    assert response.status_code == 200
    assert body["email"] is None
    assert body["emailConfirmed"] is True
    assert body["confirmationToken"] is None


async def test_duplicate_username_and_email_are_rejected(client):
    await register(client)

    duplicate_name = await register(client, email="other@example.com")
    assert duplicate_name.status_code == 409
    assert duplicate_name.json()["error"] == "Такое имя уже занято"

    duplicate_email = await register(client, username="bob")
    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["error"] == "Этот e-mail уже используется"


async def test_invalid_email_is_rejected(client):
    response = await register(client, email="not-an-email")

    assert response.status_code == 409
    assert response.json()["error"] == "Некорректный e-mail"


async def test_login_by_username_and_email(client):
    await register(client)

    by_username = await client.post(
        "/api/auth/login", json={"username": "alice", "password": DEFAULT_PASSWORD}
    )
    by_email = await client.post(
        "/api/auth/login",
        json={"username": "ALICE@example.com", "password": DEFAULT_PASSWORD},
    )

    assert by_username.status_code == 200
    assert by_email.status_code == 200
    assert by_email.json()["username"] == "alice"


async def test_login_with_wrong_password_returns_401(client):
    await register(client)

    response = await client.post(
        "/api/auth/login", json={"username": "alice", "password": "wrong-pass"}
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Неверное имя/e-mail или пароль"


async def test_confirm_email(client):
    registered = (await register(client)).json()

    response = await client.post(
        "/api/auth/confirm-email", json={"token": registered["confirmationToken"]}
    )

    assert response.status_code == 200
    assert response.json()["message"] == "E-mail подтверждён"

    profile = await client.get(
        "/api/profile", headers={"Authorization": f"Bearer {registered['token']}"}
    )
    assert profile.json()["emailConfirmed"] is True


async def test_resend_confirmation_and_forgot_password(client):
    registered = (await register(client)).json()

    resent = await client.post(
        "/api/auth/resend-confirmation", json={"email": "alice@example.com"}
    )
    assert resent.status_code == 200
    assert resent.json()["token"] != registered["confirmationToken"]

    forgot = await client.post(
        "/api/auth/forgot-password", json={"email": "alice@example.com"}
    )
    assert forgot.status_code == 200
    assert forgot.json()["token"]

    unknown = await client.post(
        "/api/auth/forgot-password", json={"email": "nobody@example.com"}
    )
    assert unknown.status_code == 200
    assert unknown.json()["token"] is None


async def test_reset_password(client):
    await register(client)
    forgot = (
        await client.post(
            "/api/auth/forgot-password", json={"email": "alice@example.com"}
        )
    ).json()

    response = await client.post(
        "/api/auth/reset-password",
        json={"token": forgot["token"], "password": "new-pass"},
    )
    assert response.status_code == 200

    old_login = await client.post(
        "/api/auth/login", json={"username": "alice", "password": DEFAULT_PASSWORD}
    )
    new_login = await client.post(
        "/api/auth/login", json={"username": "alice", "password": "new-pass"}
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


async def test_profile_requires_auth(client):
    response = await client.get("/api/profile")

    assert response.status_code == 401
    assert response.json()["error"] == "Требуется авторизация"


async def test_profile_returns_empty_statistics(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.get("/api/profile", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "username": "alice",
        "role": "PLAYER",
        "email": "alice@example.com",
        "emailConfirmed": False,
        "gamesPlayed": 0,
        "gamesWon": 0,
        "winRate": 0.0,
        "bestScore": 0,
    }


async def test_change_email(client):
    await register(client)
    headers = await auth_headers(client)

    response = await client.put(
        "/api/profile/email", headers=headers, json={"email": "new@example.com"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "E-mail изменён, нужно подтверждение"
    assert body["token"]

    profile = (await client.get("/api/profile", headers=headers)).json()
    assert profile["email"] == "new@example.com"
    assert profile["emailConfirmed"] is False


async def test_change_email_rejects_email_of_another_user(client):
    await register(client)
    await register(client, username="bob", email="bob@example.com")
    headers = await auth_headers(client)

    response = await client.put(
        "/api/profile/email", headers=headers, json={"email": "bob@example.com"}
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Этот e-mail уже используется"


async def test_default_word_bank_is_public(client):
    response = await client.get("/api/word-bank/default")

    assert response.status_code == 200
    words = response.json()
    assert len(words) == 30
    assert {"word": "КОТ", "baseScore": 9} in words
    assert {"word": "АУКЦИОН", "baseScore": 49} in words
