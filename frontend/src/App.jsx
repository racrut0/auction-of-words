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
    if (typeof user?.nick === "string" && typeof user.token === "string" && user.token) return user;
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
  const [signingOut, setSigningOut] = useState(false);
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
  const enter = ({ username, token, guest = false }) => {
    if (typeof username !== "string" || !username || typeof token !== "string" || !token) {
      throw new Error("Сервер вернул неполные данные для входа.");
    }
    const nextUser = { nick: username, token, guest };
    saveUser(nextUser);
    setUser(nextUser);
    if (!/^#lobby\/[A-Z0-9]{6}$/.test(window.location.hash)) window.location.hash = "lobby";
  };
  const logout = async () => {
    if (signingOut) return;
    setSigningOut(true);
    try {
      await lobbyService.leaveCurrent(user.token);
    } catch {
      // Сессия на устройстве закрывается даже при потере связи.
    } finally {
      saveUser(null);
      setUser(null);
      openPage(null);
      setScreen("login");
      setSigningOut(false);
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
              <button className="btn btn-outline" onClick={logout} disabled={signingOut}>Выйти</button>
            </div>
          </div>
        )}
      </header>
      <main className={currentPage === "profile" ? "profile-main" : user && !currentPage ? "app-main" : "auth-main"}>
        {currentPage === "rules" && <RulesPage onClose={() => openPage(null)} />}
        {currentPage === "connection" && <ConnectionLostPage onBack={backToLobby} />}
        {currentPage === "profile" && user && (
          <ProfilePage user={user} onSessionExpired={logout} onBack={backToLobby} />
        )}
        {!currentPage && !user && screen === "login" && (
          <LoginPage onLogin={enter} goRegister={() => setScreen("register")} />
        )}
        {!currentPage && !user && screen === "register" && (
          <RegisterPage onRegister={enter} goLogin={() => setScreen("login")} />
        )}
        {!currentPage && user && <LobbyApp user={user} onSessionExpired={logout} />}
      </main>
    </>
  );
}
