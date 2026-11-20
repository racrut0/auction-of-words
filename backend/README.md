# Бэкенд

Нужны Python и PostgreSQL. Откройте PowerShell в корне проекта и установите зависимости.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Если нужен локальный PostgreSQL, один раз выполните команду ниже. Замените путь к `bin` на путь к установленной версии.

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\dev_db.ps1 init -PgBin 'C:\Program Files\PostgreSQL\18\bin'
```

Скрипт запускает PostgreSQL на порту 5433 и создаёт базы `wordauction` и `wordauction_test`. Чтобы запустить его после остановки, используйте ту же команду с `start` вместо `init`. Если PostgreSQL уже настроен, укажите свою базу в `DATABASE_URL` в файле `.env`.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8081
```

- [Документация API](http://127.0.0.1:8081/docs)
- [Проверка подключения к БД](http://127.0.0.1:8081/api/health)

## Тесты

```powershell
.\.venv\Scripts\python.exe -m pytest
```

По умолчанию тесты подключаются к `wordauction_test` на порту 5433 и пересоздают таблицы. Если используете другой PostgreSQL или в тестовой базе осталась старая схема, укажите адрес отдельной пустой базы в `$env:TEST_DATABASE_URL`.
