import { normalizeLobbyCode } from "../lib/lobby.js";
import { request } from "./account.js";

function roomPath(code) {
  return `/lobbies/${encodeURIComponent(normalizeLobbyCode(code))}`;
}

export const lobbyService = {
  list(token, signal) {
    return request("/lobbies", { token, signal });
  },
  get(code, token, signal) {
    return request(roomPath(code), { token, signal });
  },
  create(token, settings, words) {
    return request("/lobbies", { method: "POST", token, data: { settings, words } });
  },
  join(code, token) {
    return request(`${roomPath(code)}/join`, { method: "POST", token });
  },
  setReady(code, token, ready) {
    return request(`${roomPath(code)}/ready`, { method: "PUT", token, data: { ready } });
  },
  start(code, token) {
    return request(`${roomPath(code)}/start`, { method: "POST", token });
  },
  bid(code, token, lotId, amount) {
    return request(`${roomPath(code)}/auction/bid`, { method: "PUT", token, data: { lotId, amount } });
  },
  submitWords(code, token, roundNumber, words) {
    return request(`${roomPath(code)}/words`, { method: "POST", token, data: { roundNumber, words } });
  },
  nextRound(code, token, roundNumber) {
    return request(`${roomPath(code)}/round/next`, { method: "POST", token, data: { roundNumber } });
  },
  removePlayer(code, token, playerId) {
    return request(`${roomPath(code)}/players/${playerId}`, { method: "DELETE", token });
  },
  leave(code, token) {
    return request(`${roomPath(code)}/players/me`, { method: "DELETE", token });
  },
  leaveCurrent(token) {
    return request("/lobbies/membership", { method: "DELETE", token });
  },
};
