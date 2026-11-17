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

export default function LobbyApp({ user }) {
  const [route, setRoute] = useState(readRoute);
  const lobbies = useLobbies();

  useEffect(() => {
    const update = () => { setRoute(readRoute()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);

  const back = () => { window.location.hash = "lobby"; };
  const open = (code) => { window.location.hash = `lobby/${code}`; };

  if (route.page === "create") return <CreateLobbyPage user={user} onBack={back} onCreated={open} />;
  if (route.page === "room") return <LobbyRoomPage key={route.code} user={user} lobby={lobbies.find((lobby) => lobby.code === route.code)} onBack={back} />;
  return <LobbyPage user={user} lobbies={lobbies} onCreate={() => { window.location.hash = "lobby/new"; }} onOpen={open} />;
}
