// Правила проверки полей (US-01, US-02, US-03).
export const MIN_PASSWORD = 6;
const MAX_PASSWORD = 64;
const MAX_PASSWORD_BYTES = 72;
const encoder = new TextEncoder();

export function validateNick(nick) {
  const v = nick.trim();
  if (!/^[\p{L}\p{N}_\- ]{2,20}$/u.test(v)) {
    return "Имя игрока: 2–20 символов (буквы, цифры, пробел, дефис).";
  }
  return null;
}

export function validateEmail(email) {
  const value = email.trim();
  return value.length <= 128 && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)
    ? null
    : "Введите корректный e-mail.";
}

export function validatePassword(password) {
  if ([...password].length < MIN_PASSWORD) {
    return `Пароль должен быть не короче ${MIN_PASSWORD} символов.`;
  }
  return validatePasswordLength(password);
}

function validatePasswordLength(password) {
  if ([...password].length > MAX_PASSWORD) return `Пароль должен быть не длиннее ${MAX_PASSWORD} символов.`;
  if (encoder.encode(password).length > MAX_PASSWORD_BYTES) return "Пароль слишком длинный. Сократите его.";
  return null;
}

export function validateLogin(identifier, password) {
  const value = identifier.trim();
  const length = [...value].length;
  if (length < 3) return "Введите имя игрока или e-mail.";
  if (length > 32) return "Если адрес длиннее 32 символов, войдите по имени игрока.";
  if (!password) return "Введите пароль.";
  if ([...password].length < 4) return "Пароль должен содержать хотя бы 4 символа.";
  return validatePasswordLength(password);
}

export function validateRegister({ nick, email, password, repeat }) {
  return (
    validateNick(nick) ||
    ([...nick.trim()].length < 3 ? "Имя для регистрации должно содержать минимум 3 символа." : null) ||
    validateEmail(email) ||
    validatePassword(password) ||
    (password !== repeat ? "Пароли не совпадают." : null)
  );
}
