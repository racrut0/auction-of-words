// Правила проверки полей (US-01, US-02, US-03).
export const MIN_PASSWORD = 6;

export function validateNick(nick) {
  const v = nick.trim();
  if (!/^[\p{L}\p{N}_\- ]{2,20}$/u.test(v)) {
    return "Имя игрока: 2–20 символов (буквы, цифры, пробел, дефис).";
  }
  return null;
}

export function validateEmail(email) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())
    ? null
    : "Введите корректный e-mail.";
}

export function validatePassword(password) {
  return password.length >= MIN_PASSWORD
    ? null
    : `Пароль должен быть не короче ${MIN_PASSWORD} символов.`;
}

export function validateRegister({ nick, email, password, repeat }) {
  return (
    validateNick(nick) ||
    validateEmail(email) ||
    validatePassword(password) ||
    (password !== repeat ? "Пароли не совпадают." : null)
  );
}
