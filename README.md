# Аукцион слов

Онлайн-игра, в которой игроки покупают буквы на аукционе и собирают из них слова.

## Структура

- `backend` — API на FastAPI и PostgreSQL
- `frontend` — интерфейс на React и Vite

## Запуск бэкенда

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File scripts\dev_db.ps1 init
copy .env.example .env
uvicorn app.main:app --reload --port 8081
```

Подробнее — в [backend/README.md](backend/README.md).
