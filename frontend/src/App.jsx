import { useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import RegisterPage from "./components/RegisterPage.jsx";

export default function App() {
  const [screen, setScreen] = useState("login"); // "login" | "register" | "lobby"
  const [user, setUser] = useState(null);

  const enter = (u) => {
    setUser(u);
    setScreen("lobby");
  };
  const logout = () => {
    setUser(null);
    setScreen("login");
  };

  return (
    <>
      <header className="topbar">
        <span className="brand">Аукцион слов</span>
        {user && (
          <nav>
            <span className="who">{user.nick}{user.guest ? " (гость)" : ""}</span>
            <button className="btn btn-outline" onClick={logout}>Выйти</button>
          </nav>
        )}
      </header>
      <main>
        {screen === "login" && (
          <LoginPage onLogin={enter} onGuest={enter} goRegister={() => setScreen("register")} />
        )}
        {screen === "register" && (
          <RegisterPage onRegister={enter} goLogin={() => setScreen("login")} />
        )}
        {screen === "lobby" && (
          <section className="card wide">
            <h1>Лобби</h1>
            <p>Привет, <b>{user.nick}</b>! Экран лобби — следующая задача.</p>
          </section>
        )}
      </main>
    </>
  );
}
