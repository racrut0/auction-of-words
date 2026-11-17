import { useState } from "react";
import { lobbyService } from "../../services/lobbies.js";

export default function LobbyPage({ user, lobbies, onCreate, onOpen }) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  function join(value) {
    try {
      const lobby = lobbyService.join(value, user);
      setError("");
      onOpen(lobby.code);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="lobby-page" aria-labelledby="lobby-title">
      <div className="page-heading">
        <h1 id="lobby-title">Лобби</h1>
        <p>Подключение к партии по коду или создание нового лобби</p>
      </div>

      <div className="lobby-entry-grid">
        <section className="panel join-panel" aria-labelledby="join-title">
          <h2 id="join-title">Подключение по коду</h2>
          <form className="join-form" noValidate onSubmit={(event) => { event.preventDefault(); join(code); }}>
            <label className="field" htmlFor="invitation-code">
              <span>Код приглашения</span>
              <input id="invitation-code" value={code} maxLength={6} autoComplete="off"
                spellCheck={false} aria-invalid={Boolean(error)} aria-describedby={error ? "join-error" : undefined}
                onChange={(event) => { setCode(event.target.value.toUpperCase()); setError(""); }} />
            </label>
            <button className="btn btn-primary" type="submit">Подключиться</button>
          </form>
          {error && <p className="form-error" id="join-error" role="alert">{error}</p>}
        </section>

        <section className="panel new-lobby-panel" aria-labelledby="new-lobby-title">
          <h2 id="new-lobby-title">Новая партия</h2>
          <p>Параметры игры и банк слов</p>
          <button className="btn btn-primary" onClick={onCreate}>Создать лобби</button>
        </section>
      </div>

      <section className="panel available-lobbies" aria-labelledby="available-title">
        <h2 id="available-title">Доступные лобби</h2>
        <table className="data-table lobby-table">
          <thead><tr><th>Код</th><th>Создатель</th><th>Игроки</th><th>Состояние</th><th><span className="visually-hidden">Подключение</span></th></tr></thead>
          <tbody>
            {lobbies.length === 0 && <tr><td colSpan={5} className="empty-state">Доступных лобби пока нет. Можно создать новую партию.</td></tr>}
            {lobbies.map((lobby) => {
              const creator = lobby.players.find((player) => player.id === lobby.creatorId);
              const isMember = lobby.players.some((player) => player.id === user.id);
              const isFull = lobby.players.length >= lobby.settings.maxPlayers && !isMember;
              const isStarted = lobby.status !== "waiting" && !isMember;
              return (
                <tr key={lobby.code}>
                  <td className="lobby-code">{lobby.code}</td>
                  <td>{creator?.nick ?? "—"}</td>
                  <td>{lobby.players.length} из {lobby.settings.maxPlayers}</td>
                  <td className="muted">{lobby.status === "waiting" ? "Ожидание" : "Идёт игра"}</td>
                  <td className="table-action"><button className="btn btn-primary" disabled={isFull || isStarted}
                    onClick={() => join(lobby.code)} aria-label={`Подключиться к лобби ${lobby.code}`}>
                    {isFull ? "Мест нет" : isStarted ? "Игра началась" : "Подключиться"}
                  </button></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </section>
  );
}
