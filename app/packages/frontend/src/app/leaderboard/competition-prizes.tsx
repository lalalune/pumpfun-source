"use client";

import { jsx, jsxs } from "react/jsx-runtime";
import {
  createPrizeDisplay,
  type Prize,
} from "../../components/leaderboard/original-prizes";
import { useMemoCache } from "../../components/leaderboard/original-prize-formats.mjs";
import {
  competitionRulesCopy,
  formatCompetitionAmount,
  formatCompetitionLabel,
} from "./competition-rules-model";

// Native-page providers: keep the existing English copy and precise amount
// policy. This does not select a global original NumberFormat source variant.
const number = new Intl.NumberFormat("en");
const labels: Record<string, string> = {
  "web.leaderboard.cup.tier_single": competitionRulesCopy.tier_single,
  "web.leaderboard.cup.tier_range": competitionRulesCopy.tier_range,
  "web.leaderboard.cup.tier_each": competitionRulesCopy.tier_each,
};
function translate(key: string, values: Record<string, string | number> = {}) {
  if (!Object.hasOwn(labels, key)) {
    throw new Error("Unbound competition prize label: " + key);
  }
  return formatCompetitionLabel(labels[key], values);
}
const { Tier, Heading, PrizeBadge } = createPrizeDisplay({
  jsx,
  jsxs,
  useMemoCache,
  useTranslation: () => ({ t: translate, i18n: { language: "en" } }),
  classNames: (...parts) => parts.filter(Boolean).join(" "),
  canonicalLocale: (language) => (language === "en" ? "en" : null),
  formatRank: (value) => number.format(value),
  formatAmount: ({ text }) => formatCompetitionAmount(text),
});

// Complete captured 706615.J, already recovered in the accepted prize unit.
// Rank and amount are supplied facts; this neither ranks nor allocates payouts.
const findPrize = (e: Prize[], t: number) =>
  t < 1 ? null : (e.find((e) => t >= e.rankFrom && t <= e.rankTo) ?? null);

export function CompetitionRankPrize({
  prizes,
  rank,
}: {
  prizes: Prize[];
  rank: number;
}) {
  const prize = findPrize(prizes, rank);
  return prize ? (
    <span className="max-w-full [overflow-wrap:anywhere]">
      <PrizeBadge prize={prize} />
    </span>
  ) : null;
}

export function CompetitionPrizeTiers({ prizes }: { prizes: Prize[] }) {
  return (
    <section
      aria-label={competitionRulesCopy.prize_breakdown}
      className="ranking-list [overflow-wrap:anywhere]"
      data-testid="competition-prize-tiers"
    >
      <Heading title={competitionRulesCopy.prize_breakdown} isCardTop={true} />
      {prizes.map((prize, index) => (
        <Tier
          key={`${prize.rankFrom}:${prize.rankTo}:${index}`}
          prize={prize}
        />
      ))}
    </section>
  );
}
