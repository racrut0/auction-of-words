import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db")})
    return app.test_client()


REG = {"nick": "Лис", "email": "Fox@Mail.ru", "password": "secret1", "repeat": "secret1"}


def test_lobby_requires_login(client):
    assert client.get("/").headers["Location"].endswith("/login")


def test_guest_login(client):
    r = client.post("/guest", data={"nick": "Кот"}, follow_redirects=True)
    assert "Кот" in r.text and "гость" in r.text


@pytest.mark.parametrize("nick", ["", "a", "x" * 21, "<b>"])
def test_guest_bad_nick(client, nick):
    r = client.post("/guest", data={"nick": nick})
    assert r.status_code == 200 and "Имя игрока" in r.text


def test_register_then_login(client):
    assert client.post("/register", data=REG).status_code == 302
    client.post("/logout")
    r = client.post("/login", data={"email": "fox@mail.ru", "password": "secret1"},
                    follow_redirects=True)
    assert "Лис" in r.text and "гость" not in r.text


def test_register_duplicate_and_validation(client):
    client.post("/register", data=REG)
    client.post("/logout")
    assert "уже существует" in client.post("/register", data=REG).text
    assert "не совпадают" in client.post("/register", data={**REG, "email": "a@b.ru", "repeat": "x"}).text
    assert "корректный e-mail" in client.post("/register", data={**REG, "email": "bad"}).text


def test_wrong_password(client):
    client.post("/register", data=REG)
    client.post("/logout")
    assert "Неверный" in client.post("/login", data={"email": "fox@mail.ru", "password": "no"}).text
