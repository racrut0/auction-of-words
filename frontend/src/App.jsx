import { useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import RegisterPage from "./components/RegisterPage.jsx";
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
    setScreen("login");
    window.location.hash = "";
  };

  return (
    <>
      <header className="topbar">
        <button className="brand" onClick={() => { if (user) window.location.hash = "lobby"; else setScreen("login"); }}>Аукцион слов</button>
        {user && (
          <div className="header-actions">
            <nav className="main-nav" aria-label="Основная навигация">
              <button className="active" aria-current="page" onClick={() => { window.location.hash = "lobby"; }}>Лобби</button>
              <button disabled title="Раздел пока недоступен">Правила</button>
              <button disabled title="Раздел пока недоступен">Профиль</button>
            </nav>
            <div className="session-actions">
              <span className="who">{user.nick}{user.guest ? " (гость)" : ""}</span>
              <button className="btn btn-outline" onClick={logout}>Выйти</button>
            </div>
          </div>
        )}
      </header>
      <main className={user ? "app-main" : "auth-main"}>
        {!user && screen === "login" && (
          <LoginPage onLogin={enter} onGuest={enter} goRegister={() => setScreen("register")} />
        )}
        {!user && screen === "register" && (
          <RegisterPage onRegister={enter} goLogin={() => setScreen("login")} />
        )}
        {user && <LobbyApp user={user} />}
      </main>
    </>
  );
}
