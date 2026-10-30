import type { CreatorsData } from "./types";

export const CREATOR_LEADERBOARD_LIMIT: 500;
export function creatorPageFits(
  data: Pick<CreatorsData, "totalEarners" | "pageSize" | "page">,
  count: number,
): boolean;
