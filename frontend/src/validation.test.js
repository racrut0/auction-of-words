import { describe, expect, it } from "vitest";
import { validateNick, validateEmail, validateRegister } from "./validation.js";

describe("validation", () => {
  it("ник", () => {
    expect(validateNick("Лис")).toBeNull();
    expect(validateNick("a")).not.toBeNull();
    expect(validateNick("<b>")).not.toBeNull();
    expect(validateNick("x".repeat(21))).not.toBeNull();
  });
  it("e-mail", () => {
    expect(validateEmail("a@b.ru")).toBeNull();
    expect(validateEmail("bad")).not.toBeNull();
  });
  it("регистрация", () => {
    const ok = { nick: "Лис", email: "a@b.ru", password: "secret1", repeat: "secret1" };
    expect(validateRegister(ok)).toBeNull();
    expect(validateRegister({ ...ok, repeat: "x" })).toMatch(/не совпадают/);
  });
});
