import copy from "./competition-rules-copy.json" with { type: "json" };
import type { CompetitionSummary } from "./types";

// Read-only presentation of supplied facts. These strings do not implement scoring,
// registration, eligibility enforcement, terms acceptance or prize entitlement.
export { copy as competitionRulesCopy };
export const COMPETITION_TERMS_URL =
  "https://pump.fun/docs/app-competition-terms";

function fill(
  template: string,
  values: Record<string, string | number>,
): string {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key: string) =>
    Object.hasOwn(values, key) ? String(values[key]) : match,
  );
}

function date(value: string | null): string | null {
  const time = value === null ? NaN : Date.parse(value);
  // Explicit local UTC policy avoids server/browser timezone disagreement. The
  // captured helper supplies these fields but does not fix a timezone.
  return Number.isFinite(time)
    ? new Intl.DateTimeFormat("en", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZone: "UTC",
      }).format(time)
    : null;
}

const number = new Intl.NumberFormat("en");
function amount(text: string): string {
  const trimmed = text.trim();
  if (!/^\d+(?:\.\d+)?$/.test(trimmed)) return text;
  const [whole, fraction = ""] = trimmed.split(".");
  const formatWhole = (value: bigint) => new Intl.NumberFormat("en", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
  if (!/[1-9]/.test(fraction)) return formatWhole(BigInt(whole));
  let cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0").slice(0, 2));
  if ((fraction[2] ?? "0") >= "5") cents += 1n;
  return `${formatWhole(cents / 100n)}.${(cents % 100n).toString().padStart(2, "0")}`;
}

export function competitionRules(competition: CompetitionSummary) {
  const group = competition.kind === "group";
  const registrationEnd = date(competition.registrationClosesAt);
  const end = date(competition.endsAt);
  const members = {
    min: number.format(competition.minMembers),
    max: number.format(competition.maxMembers),
  };
  const join = group
    ? registrationEnd
      ? copy.rule_join_squad
      : copy.rule_join_squad_undated
    : registrationEnd
      ? copy.rule_join_solo
      : copy.rule_join_solo_undated;
  const rules = [
    fill(join, { date: registrationEnd ?? "" }),
    copy.rule_manipulation,
    copy.rule_profit_tracked,
    ...(group ? [fill(copy.rule_squad_size, members)] : []),
    fill(end ? copy.rule_winners : copy.rule_winners_undated, {
      date: end ?? "",
    }),
    ...(group ? [copy.rule_squad_pro_rata] : []),
  ];
  const schedule: { label: string; range: string }[] = [];
  for (const [label, startValue, endValue] of [
    [
      copy.registration,
      competition.registrationOpensAt,
      competition.registrationClosesAt,
    ],
    [copy.competition_window, competition.startsAt, competition.endsAt],
  ] as const) {
    const start = date(startValue),
      finish = date(endValue);
    if (start && finish)
      schedule.push({ label, range: fill(copy.range, { start, end: finish }) });
  }
  const paidRanks = competition.prizes.reduce(
    (max, prize) => Math.max(max, prize.rankTo),
    0,
  );
  return {
    title: competition.title,
    schedule,
    scoring: competition.description.trim() || copy.scoring_default,
    entry: group ? fill(copy.entry_squad, members) : copy.entry_solo,
    entryCap:
      competition.maxEntries > 0
        ? fill(
            competition.maxEntries === 1
              ? copy.entry_cap_one
              : copy.entry_cap_other,
            { count: number.format(competition.maxEntries) },
          )
        : null,
    prizeCopy: competition.prizeCopy.trim()
      ? amount(competition.prizeCopy.trim())
      : null,
    prizes: competition.prizes.map((prize) => ({
      label:
        prize.rankTo > prize.rankFrom
          ? fill(copy.tier_range, {
              from: number.format(prize.rankFrom),
              to: number.format(prize.rankTo),
            })
          : fill(copy.tier_single, { rank: number.format(prize.rankFrom) }),
      amount:
        prize.rankTo > prize.rankFrom
          ? fill(copy.tier_each, { amount: amount(prize.amount) })
          : amount(prize.amount),
    })),
    paidRanks:
      paidRanks > 0
        ? fill(paidRanks === 1 ? copy.paid_ranks_one : copy.paid_ranks_other, {
            count: number.format(paidRanks),
          })
        : null,
    rules,
  };
}
