import { useEffect, useRef, useState } from "react";

export default function useAuthSubmit(request, onSuccess) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const activeRequest = useRef(null);

  useEffect(() => () => activeRequest.current?.abort(), []);

  async function submit(credentials) {
    if (activeRequest.current) return;
    const controller = new AbortController();
    activeRequest.current = controller;
    setPending(true);
    setError("");

    try {
      const account = await request(credentials, controller.signal);
      if (!controller.signal.aborted) onSuccess(account);
    } catch (error) {
      if (!controller.signal.aborted) setError(error.message);
    } finally {
      activeRequest.current = null;
      if (!controller.signal.aborted) setPending(false);
    }
  }

  return { submit, pending, error, setError };
}
