import { useEffect, useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import RegisterPage from "./components/RegisterPage.jsx";
import RulesPage from "./components/RulesPage.jsx";
import ConnectionLostPage from "./components/ConnectionLostPage.jsx";

const SCREENS = ["login", "register", "lobby", "rules", "connection"];
const fromHash = () => {
  const s = window.location.hash.replace("#/", "");
  return SCREENS.includes(s) ? s : "login";
};

export default function App() {
  const [screen, setScreen] = useState(fromHash); // какой экран показан
  const [prev, setPrev] = useState("login"); // куда вернуться из «Правил»
  const [user, setUser] = useState(null);

  // адрес вида /#/rules позволяет открыть любой экран напрямую
  useEffect(() => {
    window.location.hash = `/${screen}`;
  }, [screen]);
  useEffect(() => {
    const onHash = () => setScreen(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const enter = (u) => {
    setUser(u);
    setScreen("lobby");
  };
  const logout = () => {
    setUser(null);
    setScreen("login");
  };
  const openRules = () => {
    if (screen !== "rules") setPrev(screen);
    setScreen("rules");
  };
  const backHome = () => setScreen(user ? "lobby" : "login");

  return (
    <>
      <header className="topbar">
        <span className="brand">Аукцион слов</span>
        <nav>
          <button className={`btn btn-outline ${screen === "rules" ? "current" : ""}`} onClick={openRules}>
            Правила
          </button>
          {user && (
            <>
              <span className="who">{user.nick}{user.guest ? " (гость)" : ""}</span>
              <button className="btn btn-outline" onClick={logout}>Выйти</button>
            </>
          )}
        </nav>
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
            <p>Привет, <b>{user ? user.nick : "игрок"}</b>! Экран лобби — следующая задача.</p>
          </section>
        )}
        {screen === "rules" && <RulesPage onClose={() => setScreen(prev === "rules" ? "login" : prev)} />}
        {screen === "connection" && <ConnectionLostPage onBack={backHome} />}
      </main>
    </>
  );
}
