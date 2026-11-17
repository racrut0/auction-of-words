import { describe, expect, it } from "vitest";
import { DEFAULT_SETTINGS, DEFAULT_WORDS, parseWordBank, validateLobbySettings } from "./lobby.js";

describe("банк слов", () => {
  it("содержит 30 стандартных слов", () => {
    expect(DEFAULT_WORDS).toHaveLength(30);
    expect(DEFAULT_WORDS.slice(0, 3)).toEqual(["КОТ", "ДОМ", "ЛЕС"]);
  });

  it("читает строки, нормализует регистр и убирает повторения", () => {
    expect(parseWordBank("\uFEFFкот\r\nДОМ, кот; ёж ЕЖ")).toEqual(["КОТ", "ДОМ", "ЕЖ"]);
  });

  it.each(["", "   ", "кот 123", "cat", "<script>"])("отклоняет неподходящий банк: %s", (text) => {
    expect(() => parseWordBank(text)).toThrow();
  });
});

describe("параметры лобби", () => {
  it("принимает стандартные параметры и нулевой штраф", () => {
    expect(validateLobbySettings(DEFAULT_SETTINGS)).toEqual({});
    expect(validateLobbySettings({ ...DEFAULT_SETTINGS, letterPenalty: "0" })).toEqual({});
  });

  it.each([
    ["maxPlayers", "1"], ["maxPlayers", "7"], ["startingCoins", ""],
    ["startingCoins", "0"], ["rounds", "1.5"], ["rounds", "11"],
    ["letterPenalty", "-1"], ["playerOrder", "unknown"],
  ])("отклоняет неверный параметр %s = %s", (name, value) => {
    expect(validateLobbySettings({ ...DEFAULT_SETTINGS, [name]: value })[name]).toBeTruthy();
  });
});
