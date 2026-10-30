import { creatorPageFits } from "./creator-page-integrity.mjs";
export const leaderboardCategories = [
  "traders",
  "creators",
  "competitions",
] as const;

export const traderPeriods = ["daily", "weekly", "monthly"] as const;
export const traderSorts = ["combined", "realized", "unrealized"] as const;
export const creatorPeriods = ["all", "1d", "1w", "1m"] as const;
export const competitionStatuses = ["live", "upcoming", "past"] as const;

export type LeaderboardCategory = (typeof leaderboardCategories)[number];
export type TraderPeriod = (typeof traderPeriods)[number];
export type TraderSort = (typeof traderSorts)[number];
export type CreatorPeriod = (typeof creatorPeriods)[number];
export type CompetitionStatus = (typeof competitionStatuses)[number];

export type DataSource = {
  mode: "developer-api";
  label: "Pump developer API";
  fetchedAt: string;
};

export type TraderEntry = {
  rank: number;
  walletAddress: string;
  username: string | null;
  userId: string | null;
  xUsername: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  pnlUsd: number;
  pnlPercent: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
  positionsCount: number;
  lastRefreshedAtMs: number;
};

export type TradersData = {
  kind: "traders";
  entries: TraderEntry[];
  periodLabel: string;
  windowStartSec: number;
};

export type CreatorEntry = {
  rank: number;
  userId: string | null;
  username: string | null;
  walletAddress: string | null;
  wallets: string[];
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  totalPaidUsdc: number;
  payoutCount: number;
  lastPaidAt: string | null;
};

export type CreatorsData = {
  kind: "creators";
  entries: CreatorEntry[];
  totalEarners: number;
  generatedAt: string | null;
  page: number;
  pageSize: number;
};

export type CompetitionSummary = {
  id: string;
  slug: string;
  kind: string;
  title: string;
  description: string;
  prizeCopy: string;
  prizes: { rankFrom: number; rankTo: number; amount: string }[];
  minMembers: number;
  maxMembers: number;
  registrationOpensAt: string | null;
  registrationClosesAt: string | null;
  startsAt: string | null;
  endsAt: string | null;
  maxEntries: number;
  entriesCount: number;
  participants: number;
  joinable: boolean;
  phase: string;
  isFinal: boolean;
};

export type CompetitionEntry = {
  entryId: string;
  participantId: string;
  kind: string;
  rank: number;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  memberCount: number;
  membersFresh: number;
  struck: boolean;
  lastRefreshedAtMs: number;
  walletAddress: string | null;
  username: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
};

export type CompetitionsData = {
  kind: "competitions";
  upcoming: CompetitionSummary[];
  live: CompetitionSummary[];
  past: CompetitionSummary[];
};

export type CompetitionDetailData = {
  kind: "competition-detail";
  competition: CompetitionSummary;
  entries: CompetitionEntry[];
  totalRanked: number;
  builtAtMs: number;
  isFinal: boolean;
};

export type LeaderboardData =
  | TradersData
  | CreatorsData
  | CompetitionsData
  | CompetitionDetailData;

export type LeaderboardSuccess = {
  ok: true;
  data: LeaderboardData;
  source: DataSource;
};

export type LeaderboardFailure = {
  ok: false;
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
  source: {
    mode: "offline" | "developer-api";
    label: string;
  };
};

export type LeaderboardResponse = LeaderboardSuccess | LeaderboardFailure;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isSource(value: unknown): value is DataSource {
  return (
    isRecord(value) &&
    value.mode === "developer-api" &&
    value.label === "Pump developer API" &&
    typeof value.fetchedAt === "string"
  );
}

function isFailure(value: unknown): value is LeaderboardFailure {
  return (
    isRecord(value) &&
    value.ok === false &&
    isRecord(value.error) &&
    typeof value.error.code === "string" &&
    typeof value.error.message === "string" &&
    typeof value.error.retryable === "boolean" &&
    isRecord(value.source) &&
    (value.source.mode === "offline" ||
      value.source.mode === "developer-api") &&
    typeof value.source.label === "string"
  );
}

function isTraderEntry(value: unknown): value is TraderEntry {
  if (!isRecord(value)) return false;
  return (
    typeof value.rank === "number" &&
    Number.isFinite(value.rank) &&
    value.rank >= 0 &&
    typeof value.walletAddress === "string" &&
    (typeof value.username === "string" || value.username === null) &&
    (typeof value.userId === "string" || value.userId === null) &&
    (typeof value.xUsername === "string" || value.xUsername === null) &&
    typeof value.isVerified === "boolean" &&
    typeof value.verifiedBadgeVisible === "boolean" &&
    [
      value.pnlUsd,
      value.pnlPercent,
      value.realizedPnlUsd,
      value.unrealizedPnlUsd,
      value.buySpendSol,
      value.positionsCount,
      value.lastRefreshedAtMs,
    ].every((number) => typeof number === "number" && Number.isFinite(number))
  );
}

function isCreatorEntry(value: unknown): value is CreatorEntry {
  if (!isRecord(value)) return false;
  return (
    typeof value.rank === "number" &&
    Number.isFinite(value.rank) &&
    value.rank >= 0 &&
    (typeof value.userId === "string" || value.userId === null) &&
    (typeof value.username === "string" || value.username === null) &&
    (typeof value.walletAddress === "string" || value.walletAddress === null) &&
    Array.isArray(value.wallets) &&
    value.wallets.every((wallet) => typeof wallet === "string") &&
    typeof value.isVerified === "boolean" &&
    typeof value.verifiedBadgeVisible === "boolean" &&
    typeof value.totalPaidUsdc === "number" &&
    Number.isFinite(value.totalPaidUsdc) &&
    typeof value.payoutCount === "number" &&
    Number.isFinite(value.payoutCount) &&
    (typeof value.lastPaidAt === "string" || value.lastPaidAt === null)
  );
}

function isCompetitionSummary(value: unknown): value is CompetitionSummary {
  if (!isRecord(value)) return false;
  return (
    ["id", "slug", "kind", "title", "description", "prizeCopy", "phase"].every(
      (key) => typeof value[key] === "string",
    ) &&
    ["group", "person"].includes(value.kind as string) &&
    ["upcoming", "registration", "live", "ended"].includes(
      value.phase as string,
    ) &&
    ["registrationOpensAt", "registrationClosesAt", "startsAt", "endsAt"].every(
      (key) => typeof value[key] === "string" || value[key] === null,
    ) &&
    [value.maxEntries, value.entriesCount, value.participants].every(
      (number) =>
        typeof number === "number" && Number.isFinite(number) && number >= 0,
    ) &&
    [value.minMembers, value.maxMembers].every(
      (number) =>
        typeof number === "number" && Number.isFinite(number) && number >= 0,
    ) &&
    Array.isArray(value.prizes) &&
    value.prizes.length <= 100 &&
    value.prizes.every(
      (prize) =>
        isRecord(prize) &&
        [prize.rankFrom, prize.rankTo].every(
          (rank) =>
            typeof rank === "number" && Number.isFinite(rank) && rank >= 0,
        ) &&
        typeof prize.amount === "string" &&
        prize.amount.length <= 200,
    ) &&
    typeof value.joinable === "boolean" &&
    typeof value.isFinal === "boolean"
  );
}

function isCompetitionEntry(value: unknown): value is CompetitionEntry {
  if (!isRecord(value)) return false;
  return (
    ["entryId", "participantId", "kind"].every(
      (key) => typeof value[key] === "string",
    ) &&
    [
      value.rank,
      value.pnlUsd,
      value.realizedPnlUsd,
      value.unrealizedPnlUsd,
      value.memberCount,
      value.membersFresh,
      value.lastRefreshedAtMs,
    ].every(
      (number) => typeof number === "number" && Number.isFinite(number),
    ) &&
    ["group", "person"].includes(value.kind as string) &&
    [
      value.rank,
      value.memberCount,
      value.membersFresh,
      value.lastRefreshedAtMs,
    ].every((number) => typeof number === "number" && number >= 0) &&
    typeof value.struck === "boolean" &&
    (typeof value.walletAddress === "string" || value.walletAddress === null) &&
    (typeof value.username === "string" || value.username === null) &&
    typeof value.isVerified === "boolean" &&
    typeof value.verifiedBadgeVisible === "boolean"
  );
}

function isData(value: unknown): value is LeaderboardData {
  if (!isRecord(value) || typeof value.kind !== "string") return false;
  if (value.kind === "traders") {
    return (
      Array.isArray(value.entries) &&
      value.entries.length <= 100 &&
      value.entries.every(isTraderEntry) &&
      typeof value.periodLabel === "string" &&
      typeof value.windowStartSec === "number" &&
      Number.isFinite(value.windowStartSec)
    );
  }
  if (value.kind === "creators") {
    return (
      Array.isArray(value.entries) &&
      value.entries.length <= 25 &&
      value.entries.every(isCreatorEntry) &&
      typeof value.totalEarners === "number" &&
      Number.isSafeInteger(value.totalEarners) &&
      value.totalEarners >= 0 &&
      (typeof value.generatedAt === "string" || value.generatedAt === null) &&
      typeof value.page === "number" &&
      Number.isSafeInteger(value.page) &&
      value.page >= 1 &&
      typeof value.pageSize === "number" &&
      Number.isSafeInteger(value.pageSize) &&
      value.pageSize >= 1 &&
      value.pageSize <= 200 &&
      creatorPageFits({
        totalEarners: value.totalEarners,
        page: value.page,
        pageSize: value.pageSize,
      }, value.entries.length)
    );
  }
  if (value.kind === "competitions") {
    return [value.upcoming, value.live, value.past].every(
      (bucket) =>
        Array.isArray(bucket) &&
        bucket.length <= 100 &&
        bucket.every(isCompetitionSummary),
    );
  }
  if (value.kind === "competition-detail") {
    return (
      isCompetitionSummary(value.competition) &&
      Array.isArray(value.entries) &&
      value.entries.length <= 100 &&
      value.entries.every(isCompetitionEntry) &&
      typeof value.totalRanked === "number" &&
      Number.isFinite(value.totalRanked) &&
      value.totalRanked >= 0 &&
      typeof value.builtAtMs === "number" &&
      Number.isFinite(value.builtAtMs) &&
      value.builtAtMs >= 0 &&
      typeof value.isFinal === "boolean"
    );
  }
  return false;
}

export function parseLeaderboardResponse(value: unknown): LeaderboardResponse {
  if (isFailure(value)) return value;
  if (
    isRecord(value) &&
    value.ok === true &&
    isData(value.data) &&
    isSource(value.source)
  ) {
    return value as LeaderboardSuccess;
  }
  throw new Error("The leaderboard adapter returned an invalid response.");
}
