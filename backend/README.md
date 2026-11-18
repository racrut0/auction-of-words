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
