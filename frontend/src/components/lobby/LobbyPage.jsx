import { useState } from "react";
import { lobbyService } from "../../services/lobbies.js";

export default function LobbyPage({ token, query, onCreate, onOpen }) {
  const lobbies = query.data ?? [];
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [leaveError, setLeaveError] = useState("");
  const [pending, setPending] = useState(false);

  async function join(value) {
    if (pending) return;
    setPending(true);
    setError("");
    try {
      const lobby = await lobbyService.join(value, token);
      onOpen(lobby.code);
    } catch (e) {
      setError(e.message);
    } finally {
      setPending(false);
    }
  }

  async function leave(code) {
    if (pending) return;
    setPending(true);
    setLeaveError("");
    try {
      await lobbyService.leave(code, token);
      query.refresh();
    } catch (e) {
      setLeaveError(e.message);
    } finally {
      setPending(false);
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
            <button className="btn btn-primary" type="submit" disabled={pending}>Подключиться</button>
          </form>
          {error && <p className="form-error" id="join-error" role="alert">{error}</p>}
        </section>

        <section className="panel new-lobby-panel" aria-labelledby="new-lobby-title">
          <h2 id="new-lobby-title">Новая партия</h2>
          <p>Параметры игры и банк слов</p>
          <button className="btn btn-primary" onClick={onCreate} disabled={pending}>Создать лобби</button>
        </section>
      </div>

      <section className="panel available-lobbies" aria-labelledby="available-title">
        <h2 id="available-title">Доступные лобби</h2>
        {leaveError && <p className="form-error" role="alert">{leaveError}</p>}
        {query.error && <p className="form-error" role="alert">{query.error.message}{" "}
          <button className="link" onClick={() => query.refresh()}>Обновить</button>
        </p>}
        <table className="data-table lobby-table">
          <thead><tr><th>Код</th><th>Создатель</th><th>Игроки</th><th>Состояние</th><th><span className="visually-hidden">Подключение</span></th></tr></thead>
          <tbody>
            {query.loading && <tr><td colSpan={5} className="empty-state">Загрузка лобби…</td></tr>}
            {!query.loading && !query.error && lobbies.length === 0 && (
              <tr><td colSpan={5} className="empty-state">Доступных лобби пока нет. Можно создать новую партию.</td></tr>
            )}
            {lobbies.map((lobby) => {
              const { isMember } = lobby;
              const waiting = lobby.status === "LOBBY";
              const isFull = lobby.playerCount >= lobby.maxPlayers && !isMember;
              return (
                <tr key={lobby.code}>
                  <td className="lobby-code">{lobby.code}</td>
                  <td>{lobby.creatorNick}</td>
                  <td>{lobby.playerCount} из {lobby.maxPlayers}</td>
                  <td className="muted">{waiting ? "Ожидание" : "Идёт игра"}</td>
                  <td className="table-action"><div className="lobby-row-actions">
                    <button className="btn btn-primary" disabled={pending || isFull || (!waiting && !isMember)}
                      onClick={() => isMember ? onOpen(lobby.code) : join(lobby.code)}
                      aria-label={`${isMember ? "Открыть лобби" : "Подключиться к лобби"} ${lobby.code}`}>
                      {isMember ? "Открыть" : isFull ? "Мест нет" : "Подключиться"}
                    </button>
                    {isMember && <button className="btn btn-danger" type="button" disabled={pending} onClick={() => leave(lobby.code)}
                      aria-label={`Выйти из партии ${lobby.code}`}>Выйти из партии</button>}
                  </div></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </section>
  );
}
