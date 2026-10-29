import { rows, wallet } from "./competition-entry-data.mjs";
export { wallet };
// Supplied display values; not an upstream response, computed ranking or price.
export const viewerEntry = {
  ...rows[0].entry,
  realizedPnlUsd: 0.004,
  unrealizedPnlUsd: -25.5,
  buySpendSol: 2,
};
export function translateViewer(key) {
  const text = {
    "web.leaderboard.squads_unnamed_row": "fixture-unnamed-squad",
    "web.leaderboard.cup.anonymous": "fixture-anonymous",
    "web.leaderboard.you_badge": "fixture-YOU",
    "kolscan.top_charts.profit_usd_header": "fixture-PnL",
    "web.leaderboard.cup.your_squad": "fixture-your-squad",
    "kolscan.top_charts.your_rank": "fixture-your-rank",
    "kolscan.top_charts.hide_stats": "fixture-hide-stats",
    "kolscan.top_charts.show_stats": "fixture-show-stats",
  };
  if (!(key in text)) throw Error("Unobserved viewer translation key " + key);
  return text[key];
}
