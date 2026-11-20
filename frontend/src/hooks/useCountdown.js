import { useEffect, useState } from "react";

export default function useCountdown(endsAt, serverTime) {
  const [seconds, setSeconds] = useState(null);

  useEffect(() => {
    if (!endsAt || !serverTime) return;
    const deadline = performance.now() + Date.parse(endsAt) - Date.parse(serverTime);
    const tick = () => setSeconds(Math.max(0, Math.ceil((deadline - performance.now()) / 1000)));
    tick();
    const timer = window.setInterval(tick, 250);
    return () => window.clearInterval(timer);
  }, [endsAt, serverTime]);

  return seconds;
}

export function formatTime(seconds) {
  if (seconds === null) return "…";
  return [Math.floor(seconds / 60), seconds % 60].map((part) => String(part).padStart(2, "0")).join(":");
}
