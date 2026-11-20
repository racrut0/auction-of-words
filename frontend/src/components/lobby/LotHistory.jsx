import { formatCoins } from "../../lib/lobby.js";

export function lotOutcome(lot) {
  if (lot.winnerPlayerId === null) return "Без победителя";
  return `${lot.winnerNick} · ${formatCoins(lot.winningAmount)}`;
}

export default function LotHistory({ lots }) {
  if (!lots.length) return null;
  return (
    <details className="lot-history">
      <summary>Итоги торгов ({lots.length})</summary>
      <ol>{lots.map((lot) => <li key={lot.number}>
        <strong>{lot.letter}</strong><span>{lotOutcome(lot)}</span>
      </li>)}</ol>
    </details>
  );
}
