import { useEffect, useState } from "react";
import useLobbies from "../../hooks/useLobbies.js";
import LobbyPage from "./LobbyPage.jsx";
import CreateLobbyPage from "./CreateLobbyPage.jsx";
import LobbyRoomPage from "./LobbyRoomPage.jsx";

function readRoute() {
  if (window.location.hash === "#lobby/new") return { page: "create" };
  const match = window.location.hash.match(/^#lobby\/([A-Z0-9]{6})$/);
  return match ? { page: "room", code: match[1] } : { page: "list" };
}

export default function LobbyApp({ user, onSessionExpired }) {
  const [route, setRoute] = useState(readRoute);
  const query = useLobbies(user.token, route.code, route.page !== "create");

  useEffect(() => {
    const update = () => { setRoute(readRoute()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);

  const back = () => { window.location.hash = "lobby"; };
  const open = (code) => { window.location.hash = `lobby/${code}`; };

  if (query.error?.status === 401) {
    return <section className="lobby-page">
      <div className="panel missing-lobby">
        <h1>Нужно войти снова</h1>
        <p role="alert">{query.error.message}</p>
        <button className="btn btn-primary" onClick={onSessionExpired}>Войти снова</button>
      </div>
    </section>;
  }

  if (route.page === "create") return <CreateLobbyPage user={user} onBack={back} onCreated={open} />;
  if (route.page === "room") return <LobbyRoomPage key={route.code} token={user.token} query={query} onBack={back} />;
  return <LobbyPage token={user.token} query={query} onCreate={() => { window.location.hash = "lobby/new"; }} onOpen={open} />;
}
