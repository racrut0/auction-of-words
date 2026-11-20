# Аукцион слов — бэкенд

REST API для игры «Аукцион слов». Python 3.12+, FastAPI, SQLAlchemy (async), PostgreSQL.

## Требования

- Python 3.12+
- PostgreSQL 13+ (локальный, Docker не нужен)

## Запуск

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

# Создать локальный кластер PostgreSQL на порту 5433
powershell -ExecutionPolicy Bypass -File scripts\dev_db.ps1 init

copy .env.example .env
uvicorn app.main:app --reload --port 8081
```

Документация API: <http://localhost:8081/docs>, проверка состояния: <http://localhost:8081/api/health>.

Если PostgreSQL уже запущен, укажите свою строку подключения в `DATABASE_URL` и создайте БД
`wordauction` и `wordauction_test`.

Если запускаете `dev_db.ps1` с установленной версией PostgreSQL, отличной от 13, передайте
`-PgBin "C:\Program Files\PostgreSQL\18\bin"` с путём к вашей версии. Сохраните один и тот же
`JWT_SECRET` в локальном `.env`, чтобы сессии оставались действительными после перезапуска.

## Тесты

Тесты используют отдельную БД `wordauction_test` (можно переопределить через `TEST_DATABASE_URL`).

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

## API

Ответы и запросы в camelCase, ошибки возвращаются в виде `{"error": "<текст>"}`.

| Метод | Путь | Описание |
| --- | --- | --- |
| GET | `/api/health` | Проверка приложения и БД |
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход по имени или e-mail |
| POST | `/api/auth/guest` | Вход гостя по нику и выдача токена |
| POST | `/api/auth/confirm-email` | Подтверждение e-mail |
| POST | `/api/auth/resend-confirmation` | Повторная отправка токена |
| POST | `/api/auth/forgot-password` | Токен смены пароля |
| POST | `/api/auth/reset-password` | Новый пароль |
| GET | `/api/profile` | Профиль и статистика |
| PUT | `/api/profile/email` | Смена e-mail |
| GET | `/api/word-bank/default` | Стандартный банк слов |
| GET | `/api/lobbies` | Список ожидающих лобби и текущая партия игрока |
| POST | `/api/lobbies` | Создать лобби с настройками и банком слов |
| GET | `/api/lobbies/{code}` | Получить состояние своей комнаты |
| POST | `/api/lobbies/{code}/join` | Подключиться по коду |
| PUT | `/api/lobbies/{code}/ready` | Задать готовность текущего игрока |
| POST | `/api/lobbies/{code}/start` | Запустить первый раунд |
| DELETE | `/api/lobbies/{code}/players/{playerId}` | Исключить игрока до старта |
| DELETE | `/api/lobbies/{code}/players/me` | Покинуть указанную комнату |
| DELETE | `/api/lobbies/membership` | Покинуть текущую комнату |

Для защищённых запросов нужен заголовок `Authorization: Bearer <токен>`.

При старте сервер фиксирует порядок участников, ставит первый раунд и открывает этап аукциона. Лоты и ставки появятся отдельно. Рабочие таблицы `lobbies` и `lobby_players` создаются при запуске. Пустые комнаты удаляются при выходе последнего участника.

## Структура

```
app/
  api/        HTTP-роутеры
  core/       безопасность и обработка ошибок
  models/     ORM-модели
  schemas/    схемы запросов и ответов
  services/   бизнес-логика
  config.py   настройки
  database.py подключение к БД
  main.py     точка входа FastAPI
tests/        интеграционные тесты
```
