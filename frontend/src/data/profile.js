const DEMO_STATISTICS = {
  gamesPlayed: 12,
  gamesWon: 7,
  winRate: 58.3,
  bestScore: 94,
};

const EMPTY_STATISTICS = {
  gamesPlayed: 0,
  gamesWon: 0,
  winRate: 0,
  bestScore: 0,
};

export function getDemoProfile(user) {
  return {
    username: user.nick,
    email: user.email ?? null,
    emailConfirmed: user.emailConfirmed ?? false,
    guest: Boolean(user.guest),
    ...(user.guest ? EMPTY_STATISTICS : DEMO_STATISTICS),
  };
}
