export async function request(path, { method = "GET", data, token, signal } = {}) {
  const headers = { Accept: "application/json" };
  if (data) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  const timeout = AbortSignal.timeout(15000);
  let response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
      cache: "no-store",
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    const message = timeout.aborted
      ? "Сервер не ответил вовремя. Попробуйте ещё раз."
      : "Не удалось подключиться к серверу. Попробуйте ещё раз.";
    throw new Error(message);
  }

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    let message = "Не удалось выполнить запрос. Попробуйте ещё раз.";
    if (typeof result?.error === "string") message = result.error;
    else if (response.status === 422) message = "Проверьте введённые данные.";
    else if ([502, 503, 504].includes(response.status)) message = "Сервер недоступен. Попробуйте ещё раз.";
    throw Object.assign(new Error(message), { status: response.status });
  }
  if (result === null) throw new Error("Сервер вернул неожиданный ответ.");
  return result;
}

export function login(credentials, signal) {
  return request("/auth/login", { method: "POST", data: credentials, signal });
}

export function loginGuest(credentials, signal) {
  return request("/auth/guest", { method: "POST", data: credentials, signal });
}

export function register(credentials, signal) {
  return request("/auth/register", { method: "POST", data: credentials, signal });
}

export function getProfile(token, signal) {
  return request("/profile", { token, signal });
}

export function changeProfileEmail(token, email) {
  return request("/profile/email", { method: "PUT", data: { email }, token });
}
