import { useState } from "react";
import LoginPage from "./components/LoginPage.jsx";
import RegisterPage from "./components/RegisterPage.jsx";
import RulesPage from "./components/RulesPage.jsx";
import ConnectionLostPage from "./components/ConnectionLostPage.jsx";
import ProfilePage from "./components/ProfilePage.jsx";
import LobbyApp from "./components/lobby/LobbyApp.jsx";
import { getDemoProfile } from "./data/profile.js";
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
    sessionStorage.setItem(USER_SESSION_KEY, JSON.stringify(nextUser));
    setUser(nextUser);
    window.location.hash = "lobby";
  };
  const logout = () => {
    lobbyService.leave(user.id);
    sessionStorage.removeItem(USER_SESSION_KEY);
    setUser(null);
    openPage(null);
    setScreen("login");
    window.location.hash = "";
  };
  const changeEmail = (email) => {
    const nextUser = { ...user, email, emailConfirmed: false };
    sessionStorage.setItem(USER_SESSION_KEY, JSON.stringify(nextUser));
    setUser(nextUser);
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
          <ProfilePage profile={getDemoProfile(user)} onChangeEmail={changeEmail} onBack={backToLobby} />
        )}
        {!currentPage && !user && screen === "login" && (
          <LoginPage onLogin={enter} onGuest={enter} goRegister={() => setScreen("register")} />
        )}
        {!currentPage && !user && screen === "register" && (
          <RegisterPage onRegister={enter} goLogin={() => setScreen("login")} />
        )}
        {!currentPage && user && <LobbyApp user={user} />}
      </main>
    </>
  );
}
