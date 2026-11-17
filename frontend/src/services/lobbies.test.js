import { beforeEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_SETTINGS, DEFAULT_WORDS } from "../lib/lobby.js";
import { createLobbyService, LOBBIES_KEY } from "./lobbies.js";

const host = { id: "host", nick: "Лис" };
const guest = { id: "guest", nick: "Кот" };
let service;
let data;
let notify;

beforeEach(() => {
  data = new Map();
  notify = vi.fn();
  service = createLobbyService({
    storage: { getItem: (key) => data.get(key) ?? null, setItem: (key, value) => data.set(key, value) },
    notify,
  });
});

const create = (settings = DEFAULT_SETTINGS) => service.create(host, settings, DEFAULT_WORDS, "words.txt");

describe("лобби", () => {
  it("создаёт лобби с уникальным кодом, настройками и создателем", () => {
    const lobby = create();
    expect(lobby.code).toMatch(/^[A-Z0-9]{6}$/);
    expect(lobby.players).toEqual([{ ...host, ready: false }]);
    expect(lobby.settings).toEqual(DEFAULT_SETTINGS);
    expect(service.read()[0].words).toHaveLength(30);
    expect(notify).toHaveBeenCalledOnce();
  });

  it("подключает по коду без учёта регистра и не дублирует участника", () => {
    const lobby = create();
    service.join(` ${lobby.code.toLowerCase()} `, guest);
    service.join(lobby.code, guest);
    expect(service.read()[0].players).toHaveLength(2);
  });

  it("не подключает к полному или неизвестному лобби", () => {
    const lobby = create({ ...DEFAULT_SETTINGS, maxPlayers: 2 });
    service.join(lobby.code, guest);
    expect(() => service.join(lobby.code, { id: "third", nick: "Сова" })).toThrow("нет свободных мест");
    expect(() => service.join("000000", guest)).toThrow("не найдено");
    expect(() => service.join("12", guest)).toThrow("6 латинских");
  });

  it("не создаёт второе лобби для того же участника", () => {
    create();
    expect(() => create()).toThrow("Сначала нужно выйти");
  });

  it("переключает готовность только участника лобби", () => {
    const lobby = create();
    service.toggleReady(lobby.code, host.id);
    expect(service.read()[0].players[0].ready).toBe(true);
    service.toggleReady(lobby.code, host.id);
    expect(service.read()[0].players[0].ready).toBe(false);
    expect(() => service.toggleReady(lobby.code, "unknown")).toThrow("не найден");
  });

  it("разрешает исключение игрока только создателю", () => {
    const lobby = create();
    service.join(lobby.code, guest);
    expect(() => service.removePlayer(lobby.code, guest.id, host.id)).toThrow("только создатель");
    expect(() => service.removePlayer(lobby.code, host.id, host.id)).toThrow("не может исключить себя");
    service.removePlayer(lobby.code, host.id, guest.id);
    expect(service.read()[0].players).toHaveLength(1);
  });

  it("передаёт роль создателя при выходе и удаляет пустое лобби", () => {
    const lobby = create();
    service.join(lobby.code, guest);
    service.leave(host.id, lobby.code);
    expect(service.read()[0].creatorId).toBe(guest.id);
    service.leave(guest.id, lobby.code);
    expect(service.read()).toEqual([]);
  });

  it("обрабатывает повреждённые сохранённые данные", () => {
    data.set(LOBBIES_KEY, "bad json");
    expect(service.read()).toEqual([]);
    data.set(LOBBIES_KEY, JSON.stringify({ code: "ABC123" }));
    expect(service.read()).toEqual([]);
  });

  it("не создаёт лобби с неверными настройками или пустым банком", () => {
    expect(() => create({ ...DEFAULT_SETTINGS, maxPlayers: 8 })).toThrow();
    expect(() => service.create(host, DEFAULT_SETTINGS, [], "empty.txt")).toThrow("хотя бы одно");
    expect(service.read()).toEqual([]);
  });
});
