import { viewerEntry, translateViewer } from "./competition-viewer-data.mjs";
// Explicit synthetic DTO-shaped display inputs. No ranking or eligibility inference.
export const competition = {
  id: "person-fixture",
  kind: "person",
  title: "Fixture competition",
  phase: "live",
  startsAt: "2026-10-29T00:00:00Z",
  endsAt: "2026-10-30T00:00:00Z",
  prizes: [
    { rankFrom: 1, rankTo: 1, amount: "1000" },
    { rankFrom: 2, rankTo: 2, amount: "2 SOL" },
  ],
};
export const entries = [1, 2, 3].map((rank, i) => ({
  ...viewerEntry,
  entryId: "entry-" + rank,
  participantId: "participant-" + rank,
  rank,
  pnlUsd: 1000 - i * 500,
  username: "Fixture trader " + rank,
}));
export const detail = {
  competition,
  leaderboard: { entries },
  viewer: {
    entry: { ...viewerEntry, entryId: "viewer", rank: 0, pnlUsd: -0.5 },
  },
};
export const buckets = { live: [competition], upcoming: [], past: [] };
export function translateBoard(key, values = {}) {
  const fixed = {
    "web.leaderboard.cup.final_results": "fixture-final-results",
    "web.leaderboard.cup.prize_breakdown": "fixture-prize-breakdown",
    "web.leaderboard.cup.standings": "fixture-standings",
    "web.leaderboard.cup.pending_title": "fixture-pending-title",
    "web.leaderboard.cup.pending_body": "fixture-pending-body",
    "web.leaderboard.rankings_aria": "fixture-rankings",
  };
  if (key in fixed) return fixed[key];
  if (key === "profile.squads.info.member_count")
    return "fixture-members:" + values.count;
  if (key === "web.leaderboard.cup.paid_ranks")
    return "fixture-paid-ranks:" + values.count;
  if (key === "web.leaderboard.cup.tier_single")
    return "fixture-tier:" + values.rank;
  if (key === "web.leaderboard.cup.tier_range")
    return "fixture-tier:" + values.from + "-" + values.to;
  if (key === "web.leaderboard.cup.tier_each")
    return "fixture-each:" + values.amount;
  return translateViewer(key, values);
}
