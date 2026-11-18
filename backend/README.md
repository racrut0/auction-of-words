# Word Auction — backend

REST API for the «Аукцион слов» game. Python 3.12+, FastAPI, SQLAlchemy (async), PostgreSQL.

## Requirements

- Python 3.12+
- PostgreSQL 13+ (local instance is fine, Docker is not required)

## Local setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Create a local PostgreSQL cluster on port 5433 and the required databases
powershell -ExecutionPolicy Bypass -File scripts\dev_db.ps1 init

copy .env.example .env
uvicorn app.main:app --reload --port 8081
```

API docs: <http://localhost:8081/docs>, health check: <http://localhost:8081/api/health>.

If you already have PostgreSQL running, just set `DATABASE_URL` in `.env` to your database and create the
`wordauction` / `wordauction_test` databases.

## API

All responses use camelCase JSON (same contract as the previous Java backend). Business errors are
returned as `{"error": "<message>"}`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/health` | Health check including the database |
| POST | `/api/auth/register` | Register (`username`, `email`, `password`) |
| POST | `/api/auth/login` | Login by username or e-mail |
| POST | `/api/auth/confirm-email` | Confirm e-mail with a token |
| POST | `/api/auth/resend-confirmation` | Resend the confirmation token |
| POST | `/api/auth/forgot-password` | Create a password reset token |
| POST | `/api/auth/reset-password` | Set a new password |
| GET | `/api/profile` | Current user profile and statistics |
| PUT | `/api/profile/email` | Change e-mail (requires confirmation) |
| GET | `/api/word-bank/default` | Default word bank with base scores |

Authenticated endpoints expect `Authorization: Bearer <token>`.

## Tests

Tests use the separate `wordauction_test` database (override with `TEST_DATABASE_URL`).

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## Project layout

```
app/
  api/        HTTP routers (health, auth, games, auctions, build, word bank)
  core/       shared helpers and error handling
  models/     SQLAlchemy ORM models
  schemas/    Pydantic request/response schemas
  services/   business logic
  config.py   settings (environment variables / .env)
  database.py async engine and session factory
  main.py     FastAPI application factory
tests/        pytest + httpx integration tests
```
