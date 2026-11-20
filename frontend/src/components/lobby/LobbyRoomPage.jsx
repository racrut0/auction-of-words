import { useEffect, useState } from "react";
import { plural } from "../../lib/lobby.js";
import { lobbyService } from "../../services/lobbies.js";

const STEPS = [
  ["LOBBY", "Ожидание"],
  ["AUCTION", "Аукцион"],
  ["BUILDING", "Сборка слов"],
  ["ROUND_RESULTS", "Результаты"],
];

export default function LobbyRoomPage({ token, query, onBack }) {
  const lobby = query.data;
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [pending, setPending] = useState(false);
  const player = lobby?.players.find((item) => item.id === lobby.myPlayerId);

  useEffect(() => {
    if (!copied) return;
    const timeout = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timeout);
  }, [copied]);

  async function act(action, leave = false) {
    if (pending) return;
    setPending(true);
    setError("");
    try {
      const result = await action();
      if (leave) onBack();
      else query.refresh(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setPending(false);
    }
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
    <div className="panel missing-lobby">
      <h1>{query.loading ? "Загрузка лобби…" : "Комната недоступна"}</h1>
      {query.error && <p role="alert">{query.error.message}</p>}
      <div className="profile-form-actions">
        <button className="btn btn-soft" onClick={onBack}>Вернуться в лобби</button>
        {query.error && ![403, 404].includes(query.error.status) && (
          <button className="btn" onClick={() => query.refresh()}>Повторить</button>
        )}
      </div>
    </div>
  </section>;

  const isCreator = lobby.creatorId === player.id;
  const waiting = lobby.status === "LOBBY";
  const activePlayers = lobby.players.filter((item) => !item.left);
  const readyCount = activePlayers.filter((item) => item.ready).length;
  const allReady = readyCount === activePlayers.length;
  const canStart = allReady && activePlayers.length >= 2;
  const currentStep = lobby.status === "FINISHED" ? "ROUND_RESULTS" : lobby.status;

  return (
    <section className="lobby-page" aria-labelledby="room-title">
      <div className="page-heading room-heading"><h1 id="room-title">Лобби {lobby.code}</h1>
        <p>{waiting
          ? `${activePlayers.length} из ${lobby.settings.maxPlayers} мест занято`
          : `Раунд ${lobby.currentRound} из ${lobby.settings.rounds}`}</p></div>
      <ol className="game-steps" aria-label="Этапы партии">
        {STEPS.map(([status, label]) => <li key={status} className={status === currentStep ? "current" : ""}
          aria-current={status === currentStep ? "step" : undefined}>{label}</li>)}
      </ol>
      <div className="room-grid">
        <div className="room-main">
          <section className="panel players-panel" aria-labelledby="players-title"><h2 id="players-title">Игроки</h2>
            <table className="data-table players-table"><thead><tr><th>Имя</th><th>Роль</th><th>Состояние</th><th><span className="visually-hidden">Действия</span></th></tr></thead>
              <tbody>{lobby.players.map((item) => <tr key={item.id}>
                <td className={item.id === player.id ? "current-player" : ""}>{item.nick}</td>
                <td className="muted">{item.id === lobby.creatorId ? "Создатель" : "Игрок"}</td>
                <td className={item.ready && !item.left ? "ready-status" : "muted"}>
                  {item.left ? "Покинул партию" : item.ready ? "Готов" : "Не готов"}
                </td>
                <td className="table-action">{waiting && isCreator && item.id !== player.id && (
                  <button className="btn" disabled={pending}
                    onClick={() => act(() => lobbyService.removePlayer(lobby.code, token, item.id))}
                    aria-label={`Исключить игрока ${item.nick}`}>Исключить</button>
                )}</td>
              </tr>)}</tbody>
            </table>
          </section>
          {waiting ? (
            <section className="panel readiness-panel" aria-label="Готовность к партии">
              <p>{activePlayers.length === 1
                ? "Ожидание второго игрока"
                : allReady ? "Все игроки готовы" : `Готовы ${readyCount} из ${activePlayers.length}`}</p>
              <div className="readiness-actions">
                <button className={`btn${player.ready ? " btn-soft" : " btn-primary"}`} aria-pressed={player.ready}
                  disabled={pending} onClick={() => act(() => lobbyService.setReady(lobby.code, token, !player.ready))}>
                  {player.ready ? "Готов" : "Подтвердить готовность"}
                </button>
                {isCreator && <button className="btn btn-primary" disabled={!canStart || pending}
                  onClick={() => act(() => lobbyService.start(lobby.code, token))}>Начать партию</button>}
              </div>
            </section>
          ) : (
            <section className="panel readiness-panel" role="status">
              <p>Партия началась. Текущий этап — {STEPS.find(([status]) => status === currentStep)?.[1].toLowerCase()}.</p>
            </section>
          )}
          {error && <p className="form-error" role="alert">{error}</p>}
          {query.error && <p className="form-error" role="alert">{query.error.message}{" "}
            <button className="link" onClick={() => query.refresh()}>Обновить</button>
          </p>}
          <div className="page-footer-actions"><button className="btn btn-soft" type="button" onClick={onBack}>Вернуться в лобби</button>
            <button className="btn btn-danger leave-lobby" type="button" disabled={pending}
              onClick={() => act(() => lobbyService.leave(lobby.code, token), true)}>Выйти из партии</button></div>
        </div>
        <aside className="room-sidebar">
          <section className="panel party-summary" aria-labelledby="party-title"><h2 id="party-title">Партия</h2>
            <dl><div><dt>Стартовый капитал</dt><dd>{lobby.settings.startingCoins} {plural(lobby.settings.startingCoins, ["монета", "монеты", "монет"])}</dd></div>
              <div><dt>Раундов</dt><dd>{lobby.settings.rounds}</dd></div>
              <div><dt>Банк слов</dt><dd>{lobby.wordCount} {plural(lobby.wordCount, ["слово", "слова", "слов"])}</dd></div>
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
