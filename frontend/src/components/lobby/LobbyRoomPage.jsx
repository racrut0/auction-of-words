import { useEffect, useState } from "react";
import { plural } from "../../lib/lobby.js";
import { lobbyService } from "../../services/lobbies.js";

export default function LobbyRoomPage({ user, lobby, onBack }) {
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const player = lobby?.players.find((item) => item.id === user.id);

  useEffect(() => {
    if (!copied) return;
    const timeout = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timeout);
  }, [copied]);

  function act(action) {
    try { action(); setError(""); } catch (e) { setError(e.message); }
  }

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(lobby.code);
      setCopied(true);
      setError("");
    } catch {
      setError("Не удалось скопировать код. Его можно выделить и скопировать вручную.");
    }
  }

  if (!lobby || !player) return <section className="lobby-page">
    <div className="panel missing-lobby"><h1>{lobby ? "Участие в лобби завершено" : "Лобби не найдено"}</h1>
      <p>{lobby ? "Можно вернуться к списку доступных лобби." : "Лобби закрыто или код приглашения изменился."}</p>
      <button className="btn btn-soft" onClick={onBack}>Вернуться в лобби</button></div>
  </section>;

  const isCreator = lobby.creatorId === user.id;
  const readyCount = lobby.players.filter((item) => item.ready).length;
  const allReady = readyCount === lobby.players.length;

  return (
    <section className="lobby-page" aria-labelledby="room-title">
      <div className="page-heading room-heading"><h1 id="room-title">Лобби {lobby.code}</h1>
        <p>{lobby.players.length} из {lobby.settings.maxPlayers} мест занято</p></div>
      <ol className="game-steps" aria-label="Этапы партии">
        {["Ожидание", "Аукцион", "Сборка слов", "Результаты"].map((step, index) => <li key={step} className={index === 0 ? "current" : ""} aria-current={index === 0 ? "step" : undefined}>{step}</li>)}
      </ol>
      <div className="room-grid">
        <div className="room-main">
          <section className="panel players-panel" aria-labelledby="players-title"><h2 id="players-title">Игроки</h2>
            <table className="data-table players-table"><thead><tr><th>Имя</th><th>Роль</th><th>Состояние</th><th><span className="visually-hidden">Действия</span></th></tr></thead>
              <tbody>{lobby.players.map((item) => <tr key={item.id}>
                <td className={item.id === user.id ? "current-player" : ""}>{item.nick}</td>
                <td className="muted">{item.id === lobby.creatorId ? "Создатель" : "Игрок"}</td>
                <td className={item.ready ? "ready-status" : "muted"}>{item.ready ? "Готов" : "Не готов"}</td>
                <td className="table-action">{isCreator && item.id !== user.id && <button className="btn" onClick={() => act(() => lobbyService.removePlayer(lobby.code, user.id, item.id))} aria-label={`Исключить игрока ${item.nick}`}>Исключить</button>}</td>
              </tr>)}</tbody>
            </table>
          </section>
          <section className="panel readiness-panel" aria-label="Готовность к партии">
            <p>{allReady ? lobby.players.length === 1 ? "Ожидание остальных игроков" : `Все ${lobby.players.length} ${plural(lobby.players.length, ["игрок", "игрока", "игроков"])} готовы` : `Готовы ${readyCount} из ${lobby.players.length}`}</p>
            <div className="readiness-actions"><button className={`btn${player.ready ? " btn-soft" : " btn-primary"}`} aria-pressed={player.ready} onClick={() => act(() => lobbyService.toggleReady(lobby.code, user.id))}>{player.ready ? "Готов" : "Подтвердить готовность"}</button>
              {isCreator && <button className="btn btn-primary" disabled title="Начало партии пока недоступно">Начать партию</button>}</div>
          </section>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="page-footer-actions"><button className="btn btn-soft" type="button" onClick={onBack}>Вернуться в лобби</button>
            <button className="btn btn-danger leave-lobby" type="button" onClick={() => act(() => { lobbyService.leave(user.id, lobby.code); onBack(); })}>Выйти из партии</button></div>
        </div>
        <aside className="room-sidebar">
          <section className="panel party-summary" aria-labelledby="party-title"><h2 id="party-title">Партия</h2>
            <dl><div><dt>Стартовый капитал</dt><dd>{lobby.settings.startingCoins} {plural(lobby.settings.startingCoins, ["монета", "монеты", "монет"])}</dd></div>
              <div><dt>Раундов</dt><dd>{lobby.settings.rounds}</dd></div>
              <div><dt>Банк слов</dt><dd>{lobby.words.length} {plural(lobby.words.length, ["слово", "слова", "слов"])}</dd></div>
              <div><dt>Штраф за букву</dt><dd>{lobby.settings.letterPenalty} {plural(lobby.settings.letterPenalty, ["очко", "очка", "очков"])}</dd></div></dl>
          </section>
          <section className="panel invitation-panel" aria-labelledby="invitation-title"><h2 id="invitation-title">Код приглашения</h2>
            <p className="invitation-code">{lobby.code}</p><button className="btn" onClick={copyCode}>{copied ? "Код скопирован" : "Скопировать код"}</button>
          </section>
        </aside>
      </div>
    </section>
  );
}
