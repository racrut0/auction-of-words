export function getGuestProfile(nick) {
  return {
    username: nick,
    email: null,
    emailConfirmed: false,
    gamesPlayed: 0,
    gamesWon: 0,
    winRate: 0,
    bestScore: 0,
  };
}
