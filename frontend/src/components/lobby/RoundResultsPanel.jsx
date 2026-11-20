import useCountdown, { formatTime } from "../../hooks/useCountdown.js";

const score = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });

export default function RoundResultsPanel({ results, playerId, finished, pending, onNext }) {
  const seconds = useCountdown(results.endsAt, results.serverTime);
  const own = results.players.find((player) => player.playerId === playerId);
  const winners = results.players.filter((player) => results.winnerIds.includes(player.playerId));
  const first = results.players.find((player) => player.firstBonus > 0);

  return (
    <section className="panel" aria-labelledby="results-title">
      <div className="panel-toolbar">
        <h2 id="results-title">{finished ? "Итоги партии" : "Результаты раунда"}</h2>
        {!finished && <span className="auction-clock" role="timer">
          Следующий раунд через <strong>{formatTime(seconds)}</strong>
        </span>}
      </div>
      {finished && winners.length > 0 && <p className="auction-result">
        <strong>{winners.length === 1 ? "Победитель" : "Победители"}: {winners.map((player) => player.nick).join(", ")}</strong>
      </p>}
      {first && <p className="stage-caption">Первое завершение: {first.nick} (+10)</p>}
      <table className="data-table results-table">
        <thead><tr><th>Игрок</th><th>Слова</th><th>За раунд</th><th>Всего</th></tr></thead>
        <tbody>{results.players.map((player) => (
          <tr key={player.playerId}>
            <td className={player.playerId === playerId ? "current-player" : ""}>{player.nick}</td>
            <td>{player.words.map((word) => word.word).join(", ") || "Нет слов"}</td>
            <td>{score.format(player.roundPoints)}</td>
            <td>{score.format(player.totalPoints)}</td>
          </tr>
        ))}</tbody>
      </table>
      {own && <div className="round-score round-section">
        <h3>Ваш результат</h3>
        <dl>
          {own.words.map((word) => <div key={word.word}>
            <dt>{word.word}{word.unique && " (уникальное)"}</dt><dd>+{word.points}</dd>
          </div>)}
          <div><dt>Первое завершение</dt><dd>{own.firstBonus ? `+${own.firstBonus}` : "0"}</dd></div>
          <div><dt>Штраф за буквы ({own.unusedLetters})</dt><dd>{own.letterPenalty ? `−${own.letterPenalty}` : "0"}</dd></div>
          {finished && <div><dt>Бонус за монеты</dt><dd>+{score.format(own.coinBonus)}</dd></div>}
        </dl>
      </div>}
      {onNext && <button className="btn btn-primary round-section" onClick={onNext} disabled={pending || seconds === 0}>
        Следующий раунд
      </button>}
    </section>
  );
}
