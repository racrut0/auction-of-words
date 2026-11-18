const SECTIONS = [
  {
    title: "Подготовка",
    text: "В партии 2–6 игроков. Создатель задаёт капитал, число раундов и банк слов. Для запуска нужна готовность всех участников.",
  },
  {
    title: "Закрытый аукцион",
    text: "Ставки других игроков скрыты до конца торгов. Побеждает наибольшая ставка. Монеты списываются только у покупателя буквы.",
  },
  {
    title: "Сборка слов",
    text: "Слова выбираются из общего банка. Каждая буква используется один раз. После отправки выбор изменить нельзя.",
  },
  {
    title: "Очки и победитель",
    text: "Уникальное слово даёт двойные очки, первое завершение — +10. В конце партии остаток монет умножается на 0,5. За оставшиеся буквы применяется штраф.",
  },
];

export default function RulesPage({ onClose }) {
  return (
    <section className="card rules">
      <h1>Правила игры</h1>
      <div className="rules-grid">
        {SECTIONS.map((s) => (
          <article key={s.title}>
            <h2>{s.title}</h2>
            <p>{s.text}</p>
          </article>
        ))}
      </div>
      <div className="actions end">
        <button className="btn btn-primary" onClick={onClose}>Понятно</button>
      </div>
    </section>
  );
}
