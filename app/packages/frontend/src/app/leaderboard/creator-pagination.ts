import type { CreatorsData } from "./types";

/** The confirmed-payout board serves at most 500 rows, not totalEarners rows. */
export { CREATOR_LEADERBOARD_LIMIT } from "./creator-page-integrity.mjs";
import { CREATOR_LEADERBOARD_LIMIT } from "./creator-page-integrity.mjs";

export function creatorPagination(
  data: Pick<CreatorsData, "totalEarners" | "pageSize" | "page">,
) {
  const availableEarners = Math.min(
    data.totalEarners,
    CREATOR_LEADERBOARD_LIMIT,
  );
  const totalPages = Math.max(1, Math.ceil(availableEarners / data.pageSize));
  return { availableEarners, totalPages, outOfRange: data.page > totalPages };
}
