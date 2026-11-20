import { useEffect, useState } from "react";
import { lobbyService } from "../services/lobbies.js";

export default function useLobbies(token, code, enabled) {
  const [result, setResult] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    const { signal } = controller;
    let timer;
    let inFlight = false;

    async function load() {
      if (inFlight || signal.aborted) return;
      inFlight = true;
      try {
        const data = code
          ? await lobbyService.get(code, token, signal)
          : await lobbyService.list(token, signal);
        if (!signal.aborted) setResult({ token, code, data, error: null });
      } catch (error) {
        if (!signal.aborted) {
          setResult((previous) => {
            const terminal = [401, 403, 404].includes(error.status);
            const sameQuery = previous?.token === token && previous.code === code;
            return { token, code, error, data: sameQuery && !terminal ? previous.data : null };
          });
          if ([401, 403, 404].includes(error.status)) return;
        }
      } finally {
        inFlight = false;
      }
      if (!signal.aborted && !document.hidden) {
        timer = window.setTimeout(load, code ? 2000 : 5000);
      }
    }

    function onVisibilityChange() {
      window.clearTimeout(timer);
      if (!document.hidden) void load();
    }

    void load();
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [token, code, enabled, attempt]);

  const current = result?.token === token && result.code === code ? result : null;
  return {
    data: current?.data ?? null,
    error: current?.error ?? null,
    loading: !current,
    refresh: (data) => {
      if (data) setResult({ token, code, data, error: null });
      setAttempt((value) => value + 1);
    },
  };
}
