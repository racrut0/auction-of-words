import { useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import RegisterPage from "./components/RegisterPage.jsx";
import RulesPage from "./components/RulesPage.jsx";
import ConnectionLostPage from "./components/ConnectionLostPage.jsx";
import ProfilePage from "./components/ProfilePage.jsx";
import LobbyApp from "./components/lobby/LobbyApp.jsx";
import { lobbyService } from "./services/lobbies.js";

const USER_SESSION_KEY = "word-auction:user";

function readUser() {
  try {
    const user = JSON.parse(sessionStorage.getItem(USER_SESSION_KEY));
    if (typeof user?.id !== "string" || typeof user.nick !== "string") return null;
    if (user.guest === true || (typeof user.token === "string" && user.token)) return user;
    return null;
  } catch {
    return null;
  }
}

function saveUser(user) {
  try {
    if (user) sessionStorage.setItem(USER_SESSION_KEY, JSON.stringify(user));
    else sessionStorage.removeItem(USER_SESSION_KEY);
  } catch {
    // При недоступном хранилище сессия действует до обновления страницы.
  }
}

export default function App() {
  const [screen, setScreen] = useState("login");
  const [user, setUser] = useState(readUser);
  const [page, setPage] = useState(() => {
    const p = new URLSearchParams(window.location.search).get("page");
    return ["rules", "connection", "profile"].includes(p) ? p : null;
  });
  const currentPage = page === "profile" && !user ? null : page;

  const openPage = (nextPage) => {
    const url = new URL(window.location.href);
    if (nextPage) url.searchParams.set("page", nextPage);
    else url.searchParams.delete("page");
    window.history.replaceState(window.history.state, "", url);
    setPage(nextPage);
    window.scrollTo(0, 0);
  };
  const enter = (u) => {
    const nextUser = { ...u, id: crypto.randomUUID() };
    saveUser(nextUser);
    setUser(nextUser);
    window.location.hash = "lobby";
  };
  const enterAccount = ({ username, token }) => {
    if (typeof username !== "string" || !username || typeof token !== "string" || !token) {
      throw new Error("Сервер вернул неполные данные для входа.");
    }
    enter({ nick: username, token, guest: false });
  };
  const logout = () => {
    try {
      lobbyService.leave(user.id);
    } finally {
      saveUser(null);
      setUser(null);
      openPage(null);
      setScreen("login");
      window.location.hash = "";
    }
  };
  const backToLobby = () => {
    openPage(null);
    window.location.hash = "lobby";
  };

  return (
    <>
      <header className="topbar">
        <button className="brand" onClick={() => { if (user) backToLobby(); else { openPage(null); setScreen("login"); } }}>Аукцион слов</button>
        {user && (
          <div className="header-actions">
            <nav className="main-nav" aria-label="Основная навигация">
              <button className={currentPage ? "" : "active"} aria-current={currentPage ? undefined : "page"} onClick={backToLobby}>Лобби</button>
              <button className={currentPage === "rules" ? "active" : ""} aria-current={currentPage === "rules" ? "page" : undefined} onClick={() => openPage("rules")}>Правила</button>
              <button className={currentPage === "profile" ? "active" : ""} aria-current={currentPage === "profile" ? "page" : undefined} onClick={() => openPage("profile")}>Профиль</button>
            </nav>
            <div className="session-actions">
              <span className="who">{user.nick}{user.guest ? " (гость)" : ""}</span>
              <button className="btn btn-outline" onClick={logout}>Выйти</button>
            </div>
          </div>
        )}
      </header>
      <main className={currentPage === "profile" ? "profile-main" : user && !currentPage ? "app-main" : "auth-main"}>
        {currentPage === "rules" && <RulesPage onClose={() => openPage(null)} />}
        {currentPage === "connection" && <ConnectionLostPage onBack={backToLobby} />}
        {currentPage === "profile" && user && (
          <ProfilePage key={user.id} user={user} onSessionExpired={logout} onBack={backToLobby} />
        )}
        {!currentPage && !user && screen === "login" && (
          <LoginPage onLogin={enterAccount} onGuest={enter} goRegister={() => setScreen("register")} />
        )}
        {!currentPage && !user && screen === "register" && (
          <RegisterPage onRegister={enterAccount} goLogin={() => setScreen("login")} />
        )}
        {!currentPage && user && <LobbyApp user={user} />}
      </main>
    </>
  );
}
