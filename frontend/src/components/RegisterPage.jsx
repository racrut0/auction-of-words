import { useState } from "react";
import Field from "./Field.jsx";
import useAuthSubmit from "../hooks/useAuthSubmit.js";
import { register } from "../services/account.js";
import { validateRegister } from "../validation.js";

export default function RegisterPage({ onRegister, goLogin }) {
  const [form, setForm] = useState({ nick: "", email: "", password: "", repeat: "" });
  const { submit, pending, error, setError } = useAuthSubmit(register, onRegister);
  const set = (key) => (event) => {
    const value = event.target.value;
    setForm((current) => ({ ...current, [key]: value }));
  };

  const submitForm = (event) => {
    event.preventDefault();
    const err = validateRegister(form);
    if (err) {
      setError(err);
      return;
    }
    void submit({ username: form.nick.trim(), email: form.email.trim(), password: form.password });
  };

  return (
    <section className="card">
      <h1>Регистрация</h1>
      {error && <p className="error" role="alert">{error}</p>}
      <form onSubmit={submitForm} noValidate aria-busy={pending}>
        <Field label="Имя игрока" id="r-nick" value={form.nick} maxLength={20} autoComplete="username"
          onChange={set("nick")} disabled={pending} autoFocus />
        <Field label="E-mail" id="r-email" type="email" value={form.email} maxLength={128}
          autoComplete="email" onChange={set("email")} disabled={pending} />
        <Field label="Пароль" id="r-pass" type="password" value={form.password}
          autoComplete="new-password" onChange={set("password")} disabled={pending} />
        <Field label="Повтор пароля" id="r-rep" type="password" value={form.repeat}
          autoComplete="new-password" onChange={set("repeat")} disabled={pending} />
        <button className="btn btn-primary" type="submit" disabled={pending}>
          {pending ? "Создаётся аккаунт…" : "Создать аккаунт"}
        </button>
      </form>
      <p className="foot">
        Уже есть аккаунт? <button className="link" type="button" onClick={goLogin} disabled={pending}>Войти</button>
      </p>
    </section>
  );
}
