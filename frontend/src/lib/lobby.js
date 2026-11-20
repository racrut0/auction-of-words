import defaultWords from "../data/words.txt?raw";

export const DEFAULT_SETTINGS = {
  maxPlayers: 6,
  startingCoins: 100,
  rounds: 3,
  playerOrder: "random",
  letterPenalty: 2,
};

export function plural(number, forms) {
  const value = Math.abs(number) % 100;
  if (value >= 11 && value <= 19) return forms[2];
  const last = value % 10;
  if (last === 1) return forms[0];
  return last >= 2 && last <= 4 ? forms[1] : forms[2];
}

export function formatCoins(amount) {
  return `${amount} ${plural(amount, ["монета", "монеты", "монет"])}`;
}

export function parseWordBank(text) {
  const entries = text.replace(/^\uFEFF/, "").trim().split(/[\s,;]+/u).filter(Boolean);
  if (!entries.length) throw new Error("В файле нет слов.");
  if (entries.some((word) => !/^[а-яё]{2,30}$/iu.test(word))) {
    throw new Error("Нужны русские слова длиной от 2 до 30 букв, разделённые пробелами или переносами строк.");
  }
  const words = [...new Set(entries.map((word) => word.toUpperCase().replaceAll("Ё", "Е")))];
  if (words.length > 1000) throw new Error("В банке может быть не больше 1000 слов.");
  return words;
}

export const DEFAULT_WORDS = parseWordBank(defaultWords);

export function validateLobbySettings(values) {
  const errors = {};
  const limits = {
    maxPlayers: [2, 6, "Количество игроков должно быть от 2 до 6."],
    startingCoins: [1, 10000, "Стартовый капитал должен быть от 1 до 10000 монет."],
    rounds: [1, 10, "Количество раундов должно быть от 1 до 10."],
    letterPenalty: [0, 100, "Штраф должен быть от 0 до 100 очков."],
  };
  for (const [name, [min, max, message]] of Object.entries(limits)) {
    const value = Number(values[name]);
    if (String(values[name]).trim() === "" || !Number.isInteger(value) || value < min || value > max) {
      errors[name] = message;
    }
  }
  if (!["random", "join"].includes(values.playerOrder)) errors.playerOrder = "Нужно выбрать порядок игроков.";
  return errors;
}

export function normalizeLobbyCode(code) {
  return code.trim().toUpperCase();
}
