import { useEffect, useRef, useState } from "react";
import { getGuestProfile } from "../data/profile.js";
import { changeProfileEmail, getProfile } from "../services/account.js";
import { validateEmail } from "../validation.js";
import { plural } from "../lib/lobby.js";

const numberFormat = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });

export default function ProfilePage({ user, onSessionExpired, onBack }) {
  const { guest, token } = user;
  const [accountProfile, setAccountProfile] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [editing, setEditing] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const emailInput = useRef(null);
  const editButton = useRef(null);
  const formOpened = useRef(false);
  const profile = guest ? getGuestProfile(user.nick) : accountProfile;

  useEffect(() => {
    if (guest) return;
    const controller = new AbortController();
    getProfile(token, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setAccountProfile(result);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setLoadError(error);
      });
    return () => controller.abort();
  }, [guest, token, loadAttempt]);

  useEffect(() => {
    if (editing) emailInput.current?.focus();
    else if (formOpened.current) editButton.current?.focus();
  }, [editing]);

  function editEmail() {
    setEmail(profile.email ?? "");
    setError("");
    setNotice("");
    formOpened.current = true;
    setEditing(true);
  }

  function cancel() {
    if (saving) return;
    setEditing(false);
    setError("");
  }

  async function saveEmail(event) {
    event.preventDefault();
    if (saving) return;
    const nextEmail = email.trim().toLowerCase();
    const validationError = validateEmail(nextEmail);
    if (validationError) {
      setError(validationError);
      emailInput.current?.focus();
      return;
    }
    if (nextEmail === profile.email?.toLowerCase()) {
      setError("Указан текущий e-mail. Введите другой адрес.");
      emailInput.current?.focus();
      return;
    }
    setSaving(true);
    setError("");
    try {
      await changeProfileEmail(token, nextEmail);
      setAccountProfile((current) => ({
        ...current,
        email: nextEmail,
        emailConfirmed: false,
      }));
      setEditing(false);
      setNotice("Адрес электронной почты обновлён.");
    } catch (error) {
      if (error.status === 401) setLoadError(error);
      else setError(error.message);
    } finally {
      setSaving(false);
    }
  }

  function retry() {
    setLoadError(null);
    setLoadAttempt((attempt) => attempt + 1);
  }

  if (loadError || !profile) {
    return (
      <section className="card profile-feedback" aria-labelledby="profile-title">
        <h1 id="profile-title">Профиль игрока</h1>
        {loadError ? <p className="error" role="alert">{loadError.message}</p>
          : <p role="status">Загрузка профиля…</p>}
        <div className="profile-form-actions">
          {loadError?.status === 401 && (
            <button className="btn btn-primary" type="button" onClick={onSessionExpired}>Войти снова</button>
          )}
          {loadError && loadError.status !== 401 && (
            <button className="btn btn-primary" type="button" onClick={retry}>Повторить</button>
          )}
          <button className="btn btn-soft" type="button" onClick={onBack}>Вернуться в лобби</button>
        </div>
      </section>
    );
  }

  return (
    <section className="lobby-page profile-page" aria-labelledby="profile-title">
      <div className="page-heading">
        <h1 id="profile-title">Профиль игрока</h1>
        <p>Данные игрока и статистика партий</p>
      </div>

      <div className="profile-grid">
        <section className="panel profile-account" aria-labelledby="profile-account-title">
          <h2 id="profile-account-title">Данные игрока</h2>
          <dl className="profile-details">
            <div><dt>Имя игрока</dt><dd>{profile.username}</dd></div>
            <div><dt>Тип профиля</dt><dd>{guest ? "Гостевой" : "Аккаунт"}</dd></div>
            <div>
              <dt>E-mail</dt>
              <dd>
                <span>{profile.email || "Не указан"}</span>
                {profile.email && (
                  <span className={`profile-email-status${profile.emailConfirmed ? " confirmed" : ""}`}>
                    {profile.emailConfirmed ? "Подтверждён" : "Не подтверждён"}
                  </span>
                )}
              </dd>
            </div>
          </dl>

          {!guest && (
            <button className="btn profile-edit" type="button" ref={editButton}
              onClick={editEmail} disabled={editing} aria-expanded={editing}
              aria-controls={editing ? "profile-email-form" : undefined}>
              {profile.email ? "Изменить почту" : "Добавить почту"}
            </button>
          )}
          {guest && <p className="profile-note">Для добавления почты нужен аккаунт.</p>}

          {editing && (
            <form id="profile-email-form" className="profile-email-form" noValidate onSubmit={saveEmail} aria-busy={saving}
              onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); cancel(); } }}>
              <label className="field" htmlFor="profile-email">
                <span>Новый e-mail</span>
                <input id="profile-email" ref={emailInput} type="email" autoComplete="email" maxLength={128}
                  value={email} disabled={saving} aria-invalid={Boolean(error)} aria-describedby={error ? "profile-email-error" : undefined}
                  onChange={(event) => { setEmail(event.target.value); setError(""); }} />
              </label>
              {error && <p id="profile-email-error" className="field-error" role="alert">{error}</p>}
              <div className="profile-form-actions">
                <button className="btn btn-primary" type="submit" disabled={saving}>
                  {saving ? "Сохранение…" : "Сохранить"}
                </button>
                <button className="btn" type="button" onClick={cancel} disabled={saving}>Отмена</button>
              </div>
            </form>
          )}
          {notice && <p className="profile-notice" role="status">{notice}</p>}
        </section>

        <section className="panel profile-results" aria-labelledby="profile-results-title">
          <h2 id="profile-results-title">Статистика партий</h2>
          <dl className="profile-statistics">
            <div><dt>Сыграно партий</dt><dd>{numberFormat.format(profile.gamesPlayed)}</dd></div>
            <div className="profile-wins"><dt>Выиграно партий</dt><dd>{numberFormat.format(profile.gamesWon)}</dd></div>
            <div><dt>Процент побед</dt><dd>{numberFormat.format(profile.winRate)}<span className="profile-stat-unit">%</span></dd></div>
            <div><dt>Лучший результат</dt><dd>{numberFormat.format(profile.bestScore)} <span className="profile-stat-unit">{plural(profile.bestScore, ["очко", "очка", "очков"])}</span></dd></div>
          </dl>
          {profile.gamesPlayed === 0 && <p className="profile-note">Пока нет завершённых партий.</p>}
        </section>
      </div>

      <div className="page-footer-actions">
        <button className="btn btn-soft" type="button" onClick={onBack}>Вернуться в лобби</button>
      </div>
    </section>
  );
}
