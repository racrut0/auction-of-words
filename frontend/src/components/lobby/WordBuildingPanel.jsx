import { useState } from "react";
import useCountdown, { formatTime } from "../../hooks/useCountdown.js";
import LotHistory from "./LotHistory.jsx";

function countLetters(letters) {
  const counts = new Map();
  for (const letter of letters) counts.set(letter, (counts.get(letter) ?? 0) + 1);
  return counts;
}

function fits(word, available) {
  for (const [letter, count] of countLetters(word)) {
    if ((available.get(letter) ?? 0) < count) return false;
  }
  return true;
}

export default function WordBuildingPanel({ building, pending, onSubmit }) {
  const seconds = useCountdown(building.endsAt, building.serverTime);
  const [selection, setSelection] = useState([]);
  const submitted = building.submittedWords !== null;
  const selected = building.submittedWords ?? selection;
  const canAct = !submitted && !pending && seconds > 0;
  const used = countLetters(selected.join(""));
  const tiles = building.letters.map((letter) => {
    const taken = used.get(letter) ?? 0;
    if (taken > 0) used.set(letter, taken - 1);
    return { letter, used: taken > 0 };
  });
  const remaining = tiles.filter((tile) => !tile.used);
  const available = countLetters(remaining.map((tile) => tile.letter));
  const selectedWords = new Set(selected);

  function toggle(word) {
    if (!canAct) return;
    setSelection(selectedWords.has(word) ? selected.filter((item) => item !== word) : [...selected, word]);
  }

  return (
    <section className="panel" aria-labelledby="building-title">
      <div className="panel-toolbar">
        <h2 id="building-title">Сборка слов</h2>
        <span className="auction-clock" role="timer">Осталось <strong>{formatTime(seconds)}</strong></span>
      </div>
      <div className="building-letters">
        <span className="muted">Купленные буквы</span>
        {tiles.length ? <ul className="letter-tiles">{tiles.map((tile, index) =>
          <li key={index} className={tile.used ? "used" : ""}>{tile.letter}</li>
        )}</ul> : <p>Букв нет.</p>}
      </div>
      <div className="building-grid round-section">
        <section aria-labelledby="word-bank-heading">
          <h3 id="word-bank-heading">Банк слов</h3>
          <div className="building-bank">{building.wordBank.map((word) => {
            const chosen = selectedWords.has(word);
            return <button key={word} type="button" className="btn" aria-pressed={chosen}
              disabled={!canAct || (!chosen && !fits(word, available))} onClick={() => toggle(word)}>
              <strong>{word}</strong><span>{word.length ** 2}</span>
            </button>;
          })}</div>
        </section>
        <section className="building-selection" aria-labelledby="selected-words-heading">
          <h3 id="selected-words-heading">Выбранные слова</h3>
          {selected.length > 0 ? <ul>{selected.map((word) => <li key={word}>{word}</li>)}</ul>
            : <p className="muted">Слова пока не выбраны.</p>}
          <p className="stage-caption">Осталось букв: {remaining.length}</p>
          {submitted ? <p role="status">Выбор принят. Ждём остальных игроков.</p> : (
            <button className="btn btn-primary" disabled={!canAct} onClick={() => onSubmit(selection)}>
              {selection.length ? "Отправить слова" : "Завершить без слов"}
            </button>
          )}
          {!submitted && seconds === 0 && <p role="status">Подводим итоги…</p>}
        </section>
      </div>
      <LotHistory lots={building.closedLots} />
    </section>
  );
}
