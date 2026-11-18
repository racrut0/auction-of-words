import { useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import RegisterPage from "./components/RegisterPage.jsx";
import RulesPage from "./components/RulesPage.jsx";
import ConnectionLostPage from "./components/ConnectionLostPage.jsx";
import LobbyApp from "./components/lobby/LobbyApp.jsx";
import { lobbyService } from "./services/lobbies.js";

const USER_SESSION_KEY = "word-auction:user";

function readUser() {
  try {
    const user = JSON.parse(sessionStorage.getItem(USER_SESSION_KEY));
    return typeof user?.id === "string" && typeof user?.nick === "string" ? user : null;
  } catch {
    return null;
  }
}

export default function App() {
  const [screen, setScreen] = useState("login");
  const [user, setUser] = useState(readUser);
  // Страницы «Правила» и «Соединение прервано». Открываются кнопкой «Правила»
  // или адресом ?page=rules / ?page=connection (для «Соединения» кнопки пока нет).
  const [page, setPage] = useState(() => {
    const p = new URLSearchParams(window.location.search).get("page");
    return p === "rules" || p === "connection" ? p : null;
  });

  const enter = (u) => {
    const nextUser = { ...u, id: crypto.randomUUID() };
    sessionStorage.setItem(USER_SESSION_KEY, JSON.stringify(nextUser));
    setUser(nextUser);
    window.location.hash = "lobby";
  };
  const logout = () => {
    lobbyService.leave(user.id);
    sessionStorage.removeItem(USER_SESSION_KEY);
    setUser(null);
    setPage(null);
    setScreen("login");
    window.location.hash = "";
  };

  return (
    <>
      <header className="topbar">
        <button className="brand" onClick={() => { setPage(null); if (user) window.location.hash = "lobby"; else setScreen("login"); }}>Аукцион слов</button>
        {user && (
          <div className="header-actions">
            <nav className="main-nav" aria-label="Основная навигация">
              <button className={page ? "" : "active"} aria-current={page ? undefined : "page"} onClick={() => { setPage(null); window.location.hash = "lobby"; }}>Лобби</button>
              <button className={page === "rules" ? "active" : ""} aria-current={page === "rules" ? "page" : undefined} onClick={() => setPage("rules")}>Правила</button>
              <button disabled title="Раздел пока недоступен">Профиль</button>
            </nav>
            <div className="session-actions">
              <span className="who">{user.nick}{user.guest ? " (гость)" : ""}</span>
              <button className="btn btn-outline" onClick={logout}>Выйти</button>
            </div>
          </div>
        )}
      </header>
      <main className={user && !page ? "app-main" : "auth-main"}>
        {page === "rules" && <RulesPage onClose={() => setPage(null)} />}
        {page === "connection" && <ConnectionLostPage onBack={() => setPage(null)} />}
        {!page && !user && screen === "login" && (
          <LoginPage onLogin={enter} onGuest={enter} goRegister={() => setScreen("register")} />
        )}
        {!page && !user && screen === "register" && (
          <RegisterPage onRegister={enter} goLogin={() => setScreen("login")} />
        )}
        {!page && user && <LobbyApp user={user} />}
      </main>
    </>
  );
}
