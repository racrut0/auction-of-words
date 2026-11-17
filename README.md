# Аукцион слов

Запуск:
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python app.py          # http://localhost:5000
Тесты: `pytest`

Сделано: US-01 регистрация, US-02 вход по e-mail, US-03 гостевой вход (только ник).
Не сделано (Release 2): подтверждение e-mail (US-04), восстановление пароля (US-05).
