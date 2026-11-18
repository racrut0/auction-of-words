import { useState } from "react";

// Экран «Соединение прервано» (US-06, Release 3). Без бэкенда повтор — имитация.
export default function ConnectionLostPage({ gameCode = "R8M4K2", onBack }) {
  const [retrying, setRetrying] = useState(false);

  const retry = () => {
    setRetrying(true);
    // TODO: когда появится бэкенд — повторно подключиться к партии
    setTimeout(() => setRetrying(false), 1500);
  };

  return (
    <section className="card connection">
      <h1>Соединение прервано</h1>
      <p className="lead">Восстанавливается подключение к партии {gameCode}</p>
      <div className="status" role="status" aria-live="polite">
        Восстановление состояния игры…
      </div>
      <div className="actions">
        <button className="btn btn-primary" onClick={retry} disabled={retrying}>
          {retrying ? "Подключаемся…" : "Попробовать ещё раз"}
        </button>
        <button className="btn btn-soft" onClick={onBack}>Вернуться в лобби</button>
      </div>
    </section>
  );
}
