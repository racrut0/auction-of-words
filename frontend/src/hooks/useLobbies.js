import { useEffect, useState } from "react";
import { lobbyService, LOBBIES_EVENT, LOBBIES_KEY } from "../services/lobbies.js";

export default function useLobbies() {
  const [lobbies, setLobbies] = useState(() => lobbyService.read());

  useEffect(() => {
    const update = () => setLobbies(lobbyService.read());
    const onStorage = (event) => {
      if (event.key === LOBBIES_KEY || event.key === null) update();
    };
    window.addEventListener(LOBBIES_EVENT, update);
    window.addEventListener("storage", onStorage);
    update();
    return () => {
      window.removeEventListener(LOBBIES_EVENT, update);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  return lobbies;
}
