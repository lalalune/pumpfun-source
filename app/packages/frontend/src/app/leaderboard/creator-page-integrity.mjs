/** The payout producer exposes at most this many ranked rows. */
export const CREATOR_LEADERBOARD_LIMIT = 500;

/** Entries cannot exceed the selected slice; sparse and empty pages are legal. */
export function creatorPageFits(data, count) {
  const available = Math.min(data.totalEarners, CREATOR_LEADERBOARD_LIMIT);
  // Compare pages before multiplication so valid distant empty pages remain safe.
  if (data.page > Math.ceil(available / data.pageSize)) return count === 0;
  const remaining = available - (data.page - 1) * data.pageSize;
  return count <= Math.min(data.pageSize, remaining);
}
