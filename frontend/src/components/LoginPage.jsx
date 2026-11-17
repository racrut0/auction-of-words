import { useState } from "react";
import Field from "./Field.jsx";
import { validateEmail, validateNick } from "../validation.js";

export default function LoginPage({ onLogin, onGuest, goRegister }) {
  const [tab, setTab] = useState("email");
  const [error, setError] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nick, setNick] = useState("");

  const switchTab = (t) => {
    setTab(t);
    setError(null);
  };

  const submitEmail = (e) => {
    e.preventDefault();
    const err = validateEmail(email) || (password ? null : "Введите пароль.");
    setError(err);
    // TODO: когда появится бэкенд — отправить email/password на API (US-02)
    if (!err) onLogin({ nick: email.split("@")[0], guest: false });
  };

  const submitGuest = (e) => {
    e.preventDefault();
    const err = validateNick(nick);
    setError(err);
    if (!err) onGuest({ nick: nick.trim(), guest: true });
  };

  return (
    <section className="card">
      <h1>Вход в игру</h1>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "email"}
          className={tab === "email" ? "active" : ""} onClick={() => switchTab("email")}>
          E-mail
        </button>
        <button role="tab" aria-selected={tab === "guest"}
          className={tab === "guest" ? "active" : ""} onClick={() => switchTab("guest")}>
          Гостем
        </button>
      </div>

      {error && <p className="error" role="alert">{error}</p>}

      {tab === "email" ? (
        <>
          <form onSubmit={submitEmail} noValidate>
            <Field label="E-mail" id="email" type="email" value={email}
              onChange={(e) => setEmail(e.target.value)} autoFocus />
            <Field label="Пароль" id="password" type="password" value={password}
              onChange={(e) => setPassword(e.target.value)} />
            <button type="button" className="link" onClick={() => {}}>Забыли пароль?</button>
            <button className="btn btn-primary">Войти</button>
          </form>
          <p className="foot">
            Нет аккаунта?{" "}
            <button className="link" onClick={goRegister}>Зарегистрироваться</button>
          </p>
        </>
      ) : (
        <form onSubmit={submitGuest} noValidate>
          <p className="hint">Без регистрации</p>
          <Field label="Имя игрока" id="nick" value={nick} maxLength={20}
            onChange={(e) => setNick(e.target.value)} autoFocus />
          <button className="btn btn-primary">Продолжить гостем</button>
        </form>
      )}
    </section>
  );
}
