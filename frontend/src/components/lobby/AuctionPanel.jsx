import { useState } from "react";
import useCountdown, { formatTime } from "../../hooks/useCountdown.js";
import { formatCoins } from "../../lib/lobby.js";
import LotHistory, { lotOutcome } from "./LotHistory.jsx";

export default function AuctionPanel({ auction, balance, pending, onBid }) {
  const seconds = useCountdown(auction.endsAt, auction.serverTime);
  const [amount, setAmount] = useState("");
  const value = Number(amount);
  const canBid = seconds > 0 && !pending && balance > 0;
  const validAmount = Number.isInteger(value) && value >= 1 && value <= balance;
  const last = auction.closedLots.at(-1);

  function submit(event) {
    event.preventDefault();
    if (canBid && validAmount) onBid(value);
  }

  return (
    <section className="panel auction-panel" aria-labelledby="auction-title">
      <div className="panel-toolbar">
        <div>
          <h2 id="auction-title">Аукцион букв</h2>
          <p className="stage-caption">Лот {auction.number} из {auction.lotCount}</p>
        </div>
        <span className="auction-clock" role="timer">Осталось <strong>{formatTime(seconds)}</strong></span>
      </div>
      <div className="auction-details">
        <div><span>Буква лота</span><strong className="auction-letter">{auction.letter}</strong></div>
        <div><span>Ваш баланс</span><strong>{formatCoins(balance)}</strong></div>
      </div>
      <form className="auction-bid" onSubmit={submit}>
        <label className="field">Ставка в монетах
          <input type="number" inputMode="numeric" min="1" max={Math.max(1, balance)} step="1"
            value={amount} onChange={(event) => setAmount(event.target.value)} disabled={!canBid} />
        </label>
        <button className="btn btn-primary" type="submit" disabled={!canBid || !validAmount}>
          {auction.myBid === null ? "Сделать ставку" : "Обновить ставку"}
        </button>
      </form>
      <p className="auction-bid-status" role="status">
        {seconds === 0 ? "Подводим итоги…" : balance === 0 ? "Монеты закончились."
          : auction.myBid === null ? "Ставки скрыты до конца торгов."
          : `Ставка принята (${formatCoins(auction.myBid)}). Её можно изменить до конца лота.`}
      </p>
      <div className="auction-result round-section">
        <p>Ваши буквы <strong>{auction.myLetters.join(", ") || "пока нет"}</strong></p>
        {last && <p>Лот {last.number} <strong>{last.letter}</strong> · {lotOutcome(last)}</p>}
      </div>
      <LotHistory lots={auction.closedLots} />
    </section>
  );
}
