import { useState } from "react";
import Field from "./Field.jsx";
import useAuthSubmit from "../hooks/useAuthSubmit.js";
import { login, loginGuest } from "../services/account.js";
import { validateLogin, validateNick } from "../validation.js";

function loginRequest(credentials, signal) {
  if ("nick" in credentials) return loginGuest(credentials, signal);
  return login(credentials, signal);
}

export default function LoginPage({ onLogin, goRegister }) {
  const [tab, setTab] = useState("email");
  const { submit, pending, error, setError } = useAuthSubmit(loginRequest, onLogin);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [nick, setNick] = useState("");

  const switchTab = (t) => {
    setTab(t);
    setError(null);
  };

  const submitAccount = (e) => {
    e.preventDefault();
    const err = validateLogin(identifier, password);
    if (err) {
      setError(err);
      return;
    }
    void submit({ username: identifier.trim(), password });
  };

  const submitGuest = (e) => {
    e.preventDefault();
    const err = validateNick(nick);
    setError(err);
    if (!err) void submit({ nick: nick.trim() });
  };

  return (
    <section className="card">
      <h1>Вход в игру</h1>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "email"}
          className={tab === "email" ? "active" : ""} disabled={pending} onClick={() => switchTab("email")}>
          Аккаунт
        </button>
        <button role="tab" aria-selected={tab === "guest"}
          className={tab === "guest" ? "active" : ""} disabled={pending} onClick={() => switchTab("guest")}>
          Гостем
        </button>
      </div>

      {error && <p className="error" role="alert">{error}</p>}

      {tab === "email" ? (
        <>
          <form onSubmit={submitAccount} noValidate aria-busy={pending}>
            <Field label="Имя игрока или e-mail" id="login-identifier" autoComplete="username" value={identifier}
              onChange={(e) => setIdentifier(e.target.value)} disabled={pending} autoFocus />
            <Field label="Пароль" id="password" type="password" autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)} disabled={pending} />
            <button className="btn btn-primary" type="submit" disabled={pending}>
              {pending ? "Выполняется вход…" : "Войти"}
            </button>
          </form>
          <p className="foot">
            Нет аккаунта?{" "}
            <button className="link" type="button" onClick={goRegister} disabled={pending}>Зарегистрироваться</button>
          </p>
        </>
      ) : (
        <form onSubmit={submitGuest} noValidate aria-busy={pending}>
          <p className="hint">Без регистрации</p>
          <Field label="Имя игрока" id="nick" value={nick} maxLength={20}
            onChange={(e) => setNick(e.target.value)} disabled={pending} autoFocus />
          <button className="btn btn-primary" type="submit" disabled={pending}>
            {pending ? "Выполняется вход…" : "Продолжить гостем"}
          </button>
        </form>
      )}
    </section>
  );
}
