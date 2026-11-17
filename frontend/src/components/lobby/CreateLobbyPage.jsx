import { useRef, useState } from "react";
import { DEFAULT_SETTINGS, DEFAULT_WORDS, parseWordBank, plural, validateLobbySettings } from "../../lib/lobby.js";
import { lobbyService } from "../../services/lobbies.js";

function SettingField({ label, name, error, children }) {
  return <label className="field" htmlFor={name}>
    <span id={`${name}-label`}>{label}</span>
    {children}
    {error && <span className="field-error" id={`${name}-error`}>{error}</span>}
  </label>;
}

function UnitInput({ unit, ...props }) {
  return <span className="unit-input">
    <input {...props} type="number" required style={{ width: `${Math.max(1, String(props.value).length) + .5}ch` }} />
    <span>{unit}</span>
  </span>;
}

export default function CreateLobbyPage({ user, onBack, onCreated }) {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [words, setWords] = useState(DEFAULT_WORDS);
  const [fileName, setFileName] = useState("words.txt");
  const [wordError, setWordError] = useState("");
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const fileInput = useRef(null);
  const uploadSequence = useRef(0);

  function set(name, value) {
    setSettings((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
    setError("");
  }

  function inputProps(name) {
    return { id: name, value: settings[name], onChange: (event) => set(name, event.target.value),
      "aria-labelledby": `${name}-label`, "aria-invalid": Boolean(errors[name]), "aria-describedby": errors[name] ? `${name}-error` : undefined };
  }

  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const sequence = ++uploadSequence.current;
    setWordError("");
    setLoading(true);
    try {
      if (!/\.txt$/i.test(file.name)) throw new Error("Нужно выбрать текстовый файл .txt.");
      if (file.size > 512 * 1024) throw new Error("Размер файла не должен превышать 512 КБ.");
      const parsed = parseWordBank(await file.text());
      if (sequence !== uploadSequence.current) return;
      setWords(parsed);
      setFileName(file.name);
      setExpanded(false);
    } catch (e) {
      if (sequence === uploadSequence.current) setWordError(e.message);
    } finally {
      if (sequence === uploadSequence.current) setLoading(false);
      event.target.value = "";
    }
  }

  function resetWords() {
    uploadSequence.current += 1;
    setLoading(false);
    setWordError("");
    setWords(DEFAULT_WORDS);
    setFileName("words.txt");
    setExpanded(false);
  }

  function submit(event) {
    event.preventDefault();
    const nextErrors = validateLobbySettings(settings);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length || wordError || loading) return;
    try {
      const lobby = lobbyService.create(user, settings, words, fileName);
      onCreated(lobby.code);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="lobby-page" aria-labelledby="create-title">
      <div className="page-heading"><h1 id="create-title">Новая партия</h1><p>Настройки лобби</p></div>
      <div className="create-lobby-grid">
        <section className="panel settings-panel" aria-labelledby="settings-title">
          <h2 id="settings-title">Параметры партии</h2>
          <form className="settings-form" noValidate onSubmit={submit}>
            <SettingField label="Максимум игроков" name="maxPlayers" error={errors.maxPlayers}>
              <select {...inputProps("maxPlayers")}>
                {[2, 3, 4, 5, 6].map((value) => <option key={value} value={value}>{value} {plural(value, ["игрок", "игрока", "игроков"])}</option>)}
              </select>
            </SettingField>
            <div className="settings-row">
              <SettingField label="Стартовый капитал" name="startingCoins" error={errors.startingCoins}>
                <UnitInput {...inputProps("startingCoins")} min="1" max="10000" step="1" unit={plural(Number(settings.startingCoins), ["монета", "монеты", "монет"])} />
              </SettingField>
              <SettingField label="Количество раундов" name="rounds" error={errors.rounds}>
                <input {...inputProps("rounds")} type="number" min="1" max="10" step="1" required />
              </SettingField>
            </div>
            <SettingField label="Порядок игроков" name="playerOrder" error={errors.playerOrder}>
              <select {...inputProps("playerOrder")}><option value="random">Случайный</option><option value="join">По порядку входа</option></select>
            </SettingField>
            <SettingField label="Штраф за оставшуюся букву" name="letterPenalty" error={errors.letterPenalty}>
              <UnitInput {...inputProps("letterPenalty")} min="0" max="100" step="1" unit={plural(Number(settings.letterPenalty), ["очко", "очка", "очков"])} />
            </SettingField>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="btn btn-primary create-submit" type="submit" disabled={loading || Boolean(wordError)}>Создать лобби</button>
          </form>
        </section>
        <section className="panel word-bank-panel" aria-labelledby="word-bank-title">
          <div className="panel-toolbar">
            <h2 id="word-bank-title">Банк слов</h2>
            <button className="btn" type="button" onClick={() => fileInput.current?.click()}>Загрузить файл со словами</button>
            <input className="visually-hidden" ref={fileInput} type="file" accept=".txt,text/plain" aria-label="Файл банка слов" onChange={upload} tabIndex={-1} />
          </div>
          <div className="word-file" role="status"><strong>{fileName}</strong><span>{loading ? "Чтение файла…" : `Принято ${words.length} ${plural(words.length, ["слово", "слова", "слов"])}`}</span></div>
          {wordError && <div className="word-file-error"><p className="form-error" role="alert">{wordError}</p>
            <button className="link" type="button" onClick={resetWords}>Использовать стандартный банк</button></div>}
          <div className={`word-preview${expanded ? " expanded" : ""}`}>
            <table className="data-table word-table">
              <thead><tr><th>Слово</th><th>Базовые очки</th></tr></thead>
              <tbody>{(expanded ? words : words.slice(0, 6)).map((word) => <tr key={word}><td>{word}</td><td>{word.length ** 2}</td></tr>)}</tbody>
            </table>
          </div>
          {words.length > 6 && <button className="link word-more" type="button" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>
            {expanded ? "Свернуть список" : `Ещё ${words.length - 6} ${plural(words.length - 6, ["слово", "слова", "слов"])}`}
          </button>}
        </section>
      </div>
      <div className="page-footer-actions"><button className="btn btn-soft" onClick={onBack}>Вернуться в лобби</button></div>
    </section>
  );
}
