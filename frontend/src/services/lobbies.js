import { normalizeLobbyCode, validateLobbySettings } from "../lib/lobby.js";

// Локальное хранилище до подключения API.
export const LOBBIES_KEY = "word-auction:lobbies:v1";
export const LOBBIES_EVENT = "word-auction:lobbies-changed";

function makeCode(existing) {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code;
  do {
    const bytes = crypto.getRandomValues(new Uint8Array(6));
    code = [...bytes].map((byte) => alphabet[byte % alphabet.length]).join("");
  } while (existing.some((lobby) => lobby.code === code));
  return code;
}

export function createLobbyService({ storage, notify } = {}) {
  const getStorage = () => storage ?? window.localStorage;
  const announce = notify ?? (() => window.dispatchEvent(new Event(LOBBIES_EVENT)));

  function read() {
    try {
      const lobbies = JSON.parse(getStorage().getItem(LOBBIES_KEY) ?? "[]");
      if (!Array.isArray(lobbies)) return [];
      return lobbies.filter((lobby) =>
        typeof lobby?.code === "string" && lobby.settings && Array.isArray(lobby.players) && Array.isArray(lobby.words)
      );
    } catch {
      return [];
    }
  }

  function write(lobbies) {
    try {
      getStorage().setItem(LOBBIES_KEY, JSON.stringify(lobbies));
    } catch {
      throw new Error("Не удалось сохранить лобби. Проверьте доступ к хранилищу браузера.");
    }
    announce();
  }

  function find(lobbies, code) {
    const lobby = lobbies.find((item) => item.code === normalizeLobbyCode(code));
    if (!lobby) throw new Error("Лобби с таким кодом не найдено.");
    return lobby;
  }

  function checkOtherLobby(lobbies, userId, code) {
    const other = lobbies.find((lobby) => lobby.code !== code && lobby.players.some((player) => player.id === userId));
    if (other) throw new Error(`Сначала нужно выйти из лобби ${other.code}.`);
  }

  function create(user, settings, words, wordBankName) {
    const errors = validateLobbySettings(settings);
    if (Object.keys(errors).length) throw new Error(Object.values(errors)[0]);
    if (!Array.isArray(words) || !words.length) throw new Error("В банке должно быть хотя бы одно слово.");
    const lobbies = read();
    checkOtherLobby(lobbies, user.id);
    const lobby = {
      code: makeCode(lobbies),
      creatorId: user.id,
      settings: {
        maxPlayers: Number(settings.maxPlayers),
        startingCoins: Number(settings.startingCoins),
        rounds: Number(settings.rounds),
        playerOrder: settings.playerOrder,
        letterPenalty: Number(settings.letterPenalty),
      },
      words: [...words],
      wordBankName,
      players: [{ id: user.id, nick: user.nick, ready: false }],
      status: "waiting",
      createdAt: Date.now(),
    };
    write([...lobbies, lobby]);
    return lobby;
  }

  function join(code, user) {
    const normalized = normalizeLobbyCode(code);
    if (!/^[A-Z0-9]{6}$/.test(normalized)) throw new Error("Код приглашения должен содержать 6 латинских букв или цифр.");
    const lobbies = read();
    const lobby = find(lobbies, normalized);
    if (lobby.players.some((player) => player.id === user.id)) return lobby;
    if (lobby.status !== "waiting") throw new Error("Эта партия уже началась.");
    if (lobby.players.length >= lobby.settings.maxPlayers) throw new Error("В этом лобби нет свободных мест.");
    checkOtherLobby(lobbies, user.id, normalized);
    const updated = { ...lobby, players: [...lobby.players, { id: user.id, nick: user.nick, ready: false }] };
    write(lobbies.map((item) => item.code === normalized ? updated : item));
    return updated;
  }

  function toggleReady(code, userId) {
    const lobbies = read();
    const lobby = find(lobbies, code);
    if (lobby.status !== "waiting") throw new Error("Партия уже началась.");
    if (!lobby.players.some((player) => player.id === userId)) throw new Error("Участник не найден в лобби.");
    write(lobbies.map((item) => item.code === lobby.code ? {
      ...item,
      players: item.players.map((player) => player.id === userId ? { ...player, ready: !player.ready } : player),
    } : item));
  }

  function removePlayer(code, creatorId, playerId) {
    const lobbies = read();
    const lobby = find(lobbies, code);
    if (lobby.creatorId !== creatorId) throw new Error("Исключать игроков может только создатель лобби.");
    if (playerId === creatorId) throw new Error("Создатель не может исключить себя.");
    if (lobby.status !== "waiting") throw new Error("Партия уже началась.");
    write(lobbies.map((item) => item.code === lobby.code ? {
      ...item,
      players: item.players.filter((player) => player.id !== playerId),
    } : item));
  }

  function leave(userId, code) {
    const lobbies = read();
    const updated = lobbies.flatMap((lobby) => {
      if (code && lobby.code !== code) return [lobby];
      const players = lobby.players.filter((player) => player.id !== userId);
      if (!players.length) return [];
      return [{ ...lobby, players, creatorId: lobby.creatorId === userId ? players[0].id : lobby.creatorId }];
    });
    write(updated);
  }

  return { read, create, join, toggleReady, removePlayer, leave };
}

export const lobbyService = createLobbyService();
