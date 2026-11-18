import { useState } from "react";
import Field from "./Field.jsx";
import { validateRegister } from "../validation.js";

export default function RegisterPage({ onRegister, goLogin }) {
  const [form, setForm] = useState({ nick: "", email: "", password: "", repeat: "" });
  const [error, setError] = useState(null);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    const err = validateRegister(form);
    setError(err);
    // TODO: когда появится бэкенд — отправить форму на API (US-01)
    if (!err) onRegister({ nick: form.nick.trim(), email: form.email.trim().toLowerCase(), guest: false });
  };

  return (
    <section className="card">
      <h1>Регистрация</h1>
      {error && <p className="error" role="alert">{error}</p>}
      <form onSubmit={submit} noValidate>
        <Field label="Имя игрока" id="r-nick" value={form.nick} maxLength={20}
          onChange={set("nick")} autoFocus />
        <Field label="E-mail" id="r-email" type="email" value={form.email} onChange={set("email")} />
        <Field label="Пароль" id="r-pass" type="password" value={form.password} onChange={set("password")} />
        <Field label="Повтор пароля" id="r-rep" type="password" value={form.repeat} onChange={set("repeat")} />
        <p className="hint">На указанный e-mail придёт письмо с подтверждением.</p>
        <button className="btn btn-primary">Создать аккаунт</button>
      </form>
      <p className="foot">
        Уже есть аккаунт? <button className="link" onClick={goLogin}>Войти</button>
      </p>
    </section>
  );
}
