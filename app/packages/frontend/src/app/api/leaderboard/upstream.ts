import type {
  CompetitionDetailData,
  CompetitionEntry,
  CompetitionSummary,
  CompetitionsData,
  CreatorEntry,
  CreatorsData,
  LeaderboardData,
  TraderEntry,
  TradersData,
} from "../../leaderboard/types";

export const DEVELOPER_API_ORIGIN = "https://api.pump.fun";
export const MAX_UPSTREAM_BYTES = 512 * 1024;
export const CREATOR_PAGE_SIZE = 20;

export class UpstreamValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UpstreamValidationError";
  }
}

type RecordValue = Record<string, unknown>;

function record(value: unknown, label: string): RecordValue {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new UpstreamValidationError(`${label} must be an object.`);
  }
  return value as RecordValue;
}

function array(value: unknown, label: string, maximum: number): unknown[] {
  if (!Array.isArray(value) || value.length > maximum) {
    throw new UpstreamValidationError(
      `${label} must be an array with at most ${maximum} entries.`,
    );
  }
  // Array.prototype.map/forEach skip holes, so a sparse array would pass
  // validation and come back with the hole preserved in the typed result:
  // a consumer indexing that slot reads undefined instead of the promised
  // entry. Reject any missing index, the same dense-list admission the
  // backend stores enforce (user-trades sparse-array fix).
  for (let index = 0; index < value.length; index++) {
    if (!Object.hasOwn(value, index)) {
      throw new UpstreamValidationError(
        `${label} must be a dense array without holes.`,
      );
    }
  }
  return value;
}

function text(value: unknown, label: string, maximum = 2048): string {
  if (typeof value !== "string" || value.length > maximum) {
    throw new UpstreamValidationError(`${label} must be a bounded string.`);
  }
  return value;
}

function nullableText(
  value: unknown,
  label: string,
  maximum = 2048,
): string | null {
  return value === null ? null : text(value, label, maximum);
}

function number(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new UpstreamValidationError(`${label} must be a finite number.`);
  }
  return value;
}

function nonNegativeNumber(value: unknown, label: string): number {
  const parsed = number(value, label);
  if (parsed < 0) {
    throw new UpstreamValidationError(`${label} cannot be negative.`);
  }
  return parsed;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new UpstreamValidationError(`${label} must be a boolean.`);
  }
  return value;
}

function date(value: unknown, label: string): string | null {
  const parsed = nullableText(value, label, 80);
  const parts = parsed?.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/,
  );
  const calendar = parts
    ? new Date(`${parts[1]}-${parts[2]}-${parts[3]}T00:00:00Z`)
    : null;
  if (
    parsed !== null &&
    (!parts ||
      !Number.isFinite(Date.parse(parsed)) ||
      Number(parts[4]) > 23 ||
      Number(parts[5]) > 59 ||
      Number(parts[6]) > 59 ||
      calendar?.toISOString().slice(0, 10) !== parsed.slice(0, 10))
  ) {
    throw new UpstreamValidationError(`${label} must be an ISO date.`);
  }
  return parsed;
}

function validateTopPositions(value: unknown, label: string): void {
  for (const [index, positionValue] of array(value, label, 5).entries()) {
    const position = record(positionValue, `${label}[${index}]`);
    text(position.mint, `${label}[${index}].mint`, 256);
    number(position.chainId, `${label}[${index}].chainId`);
    nullableText(position.symbol, `${label}[${index}].symbol`, 100);
    nullableText(position.name, `${label}[${index}].name`, 500);
    nullableText(position.imageUri, `${label}[${index}].imageUri`, 2048);
  }
}

function parseTraderEntry(value: unknown, index: number): TraderEntry {
  const row = record(value, `entries[${index}]`);
  validateTopPositions(row.topPositions, `entries[${index}].topPositions`);
  number(row.pnlSol, `entries[${index}].pnlSol`);
  number(row.realizedPnlSol, `entries[${index}].realizedPnlSol`);
  number(row.unrealizedPnlSol, `entries[${index}].unrealizedPnlSol`);
  nullableText(row.profileImage, `entries[${index}].profileImage`, 2048);
  return {
    rank: nonNegativeNumber(row.rank, `entries[${index}].rank`),
    walletAddress: text(
      row.walletAddress,
      `entries[${index}].walletAddress`,
      256,
    ),
    username: nullableText(row.username, `entries[${index}].username`, 200),
    userId: nullableText(row.userId, `entries[${index}].userId`, 200),
    xUsername: nullableText(row.xUsername, `entries[${index}].xUsername`, 200),
    isVerified: boolean(row.isVerified, `entries[${index}].isVerified`),
    verifiedBadgeVisible: boolean(
      row.verifiedBadgeVisible,
      `entries[${index}].verifiedBadgeVisible`,
    ),
    pnlUsd: number(row.pnlUsd, `entries[${index}].pnlUsd`),
    pnlPercent: number(row.pnlPercent, `entries[${index}].pnlPercent`),
    realizedPnlUsd: number(
      row.realizedPnlUsd,
      `entries[${index}].realizedPnlUsd`,
    ),
    unrealizedPnlUsd: number(
      row.unrealizedPnlUsd,
      `entries[${index}].unrealizedPnlUsd`,
    ),
    buySpendSol: nonNegativeNumber(
      row.buySpendSol,
      `entries[${index}].buySpendSol`,
    ),
    positionsCount: nonNegativeNumber(
      row.positionsCount,
      `entries[${index}].positionsCount`,
    ),
    lastRefreshedAtMs: nonNegativeNumber(
      row.lastRefreshedAtMs,
      `entries[${index}].lastRefreshedAtMs`,
    ),
  };
}

function parseTraders(value: unknown): TradersData {
  const payload = record(value, "trader leaderboard");
  // The response uses a numeric enum; daily/weekly/monthly are request values.
  // See OpenAPI 0.294.0 GET /pnl-leaderboard, 200 response periodType.
  const periodType = number(payload.periodType, "periodType");
  if (![0, 1, 2, 3].includes(periodType)) {
    throw new UpstreamValidationError("periodType is unsupported.");
  }
  return {
    kind: "traders",
    entries: array(payload.entries, "entries", 100).map(parseTraderEntry),
    periodLabel: text(payload.periodLabel, "periodLabel", 200),
    windowStartSec: nonNegativeNumber(payload.windowStartSec, "windowStartSec"),
  };
}

function parseCreatorEntry(value: unknown, index: number): CreatorEntry {
  const row = record(value, `entries[${index}]`);
  nullableText(row.profileImageUrl, `entries[${index}].profileImageUrl`, 2048);
  nullableText(row.twitterId, `entries[${index}].twitterId`, 200);
  nullableText(row.twitterUrl, `entries[${index}].twitterUrl`, 2048);
  const wallets = array(row.wallets, `entries[${index}].wallets`, 100).map(
    (wallet, walletIndex) =>
      text(wallet, `entries[${index}].wallets[${walletIndex}]`, 256),
  );
  if (wallets.length === 0) {
    throw new UpstreamValidationError(
      `entries[${index}].wallets must include at least one wallet.`,
    );
  }
  return {
    rank: nonNegativeNumber(row.rank, `entries[${index}].rank`),
    userId: nullableText(row.userId, `entries[${index}].userId`, 200),
    username: nullableText(row.username, `entries[${index}].username`, 200),
    walletAddress: nullableText(
      row.walletAddress,
      `entries[${index}].walletAddress`,
      256,
    ),
    wallets,
    isVerified: boolean(row.isVerified, `entries[${index}].isVerified`),
    verifiedBadgeVisible: boolean(
      row.verifiedBadgeVisible,
      `entries[${index}].verifiedBadgeVisible`,
    ),
    totalPaidUsdc: nonNegativeNumber(
      row.totalPaidUsdc,
      `entries[${index}].totalPaidUsdc`,
    ),
    payoutCount: nonNegativeNumber(
      row.payoutCount,
      `entries[${index}].payoutCount`,
    ),
    lastPaidAt: date(row.lastPaidAt, `entries[${index}].lastPaidAt`),
  };
}

function parseCreators(value: unknown, page: number): CreatorsData {
  const payload = record(value, "creator payout leaderboard");
  return {
    kind: "creators",
    entries: array(payload.entries, "entries", CREATOR_PAGE_SIZE).map(
      parseCreatorEntry,
    ),
    totalEarners: nonNegativeNumber(payload.totalEarners, "totalEarners"),
    generatedAt: date(payload.generatedAt, "generatedAt"),
    page,
    pageSize: CREATOR_PAGE_SIZE,
  };
}

function parseCompetitionPrizes(
  value: unknown,
  label: string,
): CompetitionSummary["prizes"] {
  return array(value, label, 100).map((prizeValue, index) => {
    const prize = record(prizeValue, `${label}[${index}]`);
    return {
      rankFrom: nonNegativeNumber(
        prize.rankFrom,
        `${label}[${index}].rankFrom`,
      ),
      rankTo: nonNegativeNumber(prize.rankTo, `${label}[${index}].rankTo`),
      amount: text(prize.amount, `${label}[${index}].amount`, 200),
    };
  });
}

function parseCompetitionEntry(
  value: unknown,
  label: string,
): CompetitionEntry {
  const row = record(value, label);
  const kind = text(row.kind, `${label}.kind`, 40);
  if (kind !== "group" && kind !== "person") {
    throw new UpstreamValidationError(`${label}.kind is unsupported.`);
  }
  validateTopPositions(row.topPositions, `${label}.topPositions`);
  nonNegativeNumber(row.buySpendSol, `${label}.buySpendSol`);
  nonNegativeNumber(row.positionsCount, `${label}.positionsCount`);
  nullableText(row.profileImageUrl, `${label}.profileImageUrl`, 2048);
  return {
    entryId: text(row.entryId, `${label}.entryId`, 200),
    participantId: text(row.participantId, `${label}.participantId`, 200),
    kind,
    rank: nonNegativeNumber(row.rank, `${label}.rank`),
    pnlUsd: number(row.pnlUsd, `${label}.pnlUsd`),
    realizedPnlUsd: number(row.realizedPnlUsd, `${label}.realizedPnlUsd`),
    unrealizedPnlUsd: number(row.unrealizedPnlUsd, `${label}.unrealizedPnlUsd`),
    memberCount: nonNegativeNumber(row.memberCount, `${label}.memberCount`),
    membersFresh: nonNegativeNumber(row.membersFresh, `${label}.membersFresh`),
    struck: boolean(row.struck, `${label}.struck`),
    lastRefreshedAtMs: nonNegativeNumber(
      row.lastRefreshedAtMs,
      `${label}.lastRefreshedAtMs`,
    ),
    walletAddress: nullableText(
      row.walletAddress,
      `${label}.walletAddress`,
      256,
    ),
    username: nullableText(row.username, `${label}.username`, 200),
    isVerified: boolean(row.isVerified, `${label}.isVerified`),
    verifiedBadgeVisible: boolean(
      row.verifiedBadgeVisible,
      `${label}.verifiedBadgeVisible`,
    ),
  };
}

function parseCompetitionSummary(
  value: unknown,
  label: string,
): CompetitionSummary {
  const competition = record(value, label);
  const kind = text(competition.kind, `${label}.kind`, 40);
  if (kind !== "group" && kind !== "person") {
    throw new UpstreamValidationError(`${label}.kind is unsupported.`);
  }
  const phase = text(competition.phase, `${label}.phase`, 40);
  if (!["upcoming", "registration", "live", "ended"].includes(phase)) {
    throw new UpstreamValidationError(`${label}.phase is unsupported.`);
  }
  const prizes = parseCompetitionPrizes(competition.prizes, `${label}.prizes`);
  nullableText(competition.imageUrl, `${label}.imageUrl`, 2048);
  for (const key of ["top", "winners"] as const) {
    array(competition[key], `${label}.${key}`, 100).forEach((entry, index) =>
      parseCompetitionEntry(entry, `${label}.${key}[${index}]`),
    );
  }
  return {
    id: text(competition.id, `${label}.id`, 200),
    slug: text(competition.slug, `${label}.slug`, 200),
    kind,
    title: text(competition.title, `${label}.title`, 500),
    description: text(competition.description, `${label}.description`, 5000),
    prizeCopy: text(competition.prizeCopy, `${label}.prizeCopy`, 1000),
    prizes,
    minMembers: nonNegativeNumber(
      competition.minMembers,
      `${label}.minMembers`,
    ),
    maxMembers: nonNegativeNumber(
      competition.maxMembers,
      `${label}.maxMembers`,
    ),
    registrationOpensAt: date(
      competition.registrationOpensAt,
      `${label}.registrationOpensAt`,
    ),
    registrationClosesAt: date(
      competition.registrationClosesAt,
      `${label}.registrationClosesAt`,
    ),
    startsAt: date(competition.startsAt, `${label}.startsAt`),
    endsAt: date(competition.endsAt, `${label}.endsAt`),
    maxEntries: nonNegativeNumber(
      competition.maxEntries,
      `${label}.maxEntries`,
    ),
    entriesCount: nonNegativeNumber(
      competition.entriesCount,
      `${label}.entriesCount`,
    ),
    participants: nonNegativeNumber(
      competition.participants,
      `${label}.participants`,
    ),
    joinable: boolean(competition.joinable, `${label}.joinable`),
    phase,
    isFinal: boolean(competition.isFinal, `${label}.isFinal`),
  };
}

function parseCompetitionBucket(
  value: unknown,
  label: string,
  maximum: number,
): CompetitionSummary[] {
  return array(value, label, maximum).map((competition, index) =>
    parseCompetitionSummary(competition, `${label}[${index}]`),
  );
}

function parseCompetitions(value: unknown): CompetitionsData {
  const payload = record(value, "competitions");
  return {
    kind: "competitions",
    upcoming: parseCompetitionBucket(payload.upcoming, "upcoming", 100),
    live: parseCompetitionBucket(payload.live, "live", 100),
    past: parseCompetitionBucket(payload.past, "past", 50),
  };
}

function parseCompetitionDetail(value: unknown): CompetitionDetailData {
  const payload = record(value, "competition detail");
  const board = record(payload.leaderboard, "leaderboard");
  nonNegativeNumber(board.startSec, "leaderboard.startSec");
  nonNegativeNumber(board.endSec, "leaderboard.endSec");
  return {
    kind: "competition-detail",
    competition: parseCompetitionSummary(payload.competition, "competition"),
    entries: array(board.entries, "leaderboard.entries", 100).map(
      (entry, index) =>
        parseCompetitionEntry(entry, `leaderboard.entries[${index}]`),
    ),
    totalRanked: nonNegativeNumber(
      board.totalRanked,
      "leaderboard.totalRanked",
    ),
    builtAtMs: nonNegativeNumber(board.builtAtMs, "leaderboard.builtAtMs"),
    isFinal: boolean(board.isFinal, "leaderboard.isFinal"),
  };
}

export function normalizeUpstreamResponse(
  category: "traders" | "creators" | "competitions",
  value: unknown,
  options: { page: number; competitionId: string | null },
): LeaderboardData {
  if (category === "traders") return parseTraders(value);
  if (category === "creators") return parseCreators(value, options.page);
  if (!options.competitionId) return parseCompetitions(value);
  const detail = parseCompetitionDetail(value);
  if (
    detail.competition.id !== options.competitionId &&
    detail.competition.slug.toLowerCase() !== options.competitionId.toLowerCase()
  ) {
    throw new UpstreamValidationError(
      "The returned competition does not match the requested id or slug.",
    );
  }
  return detail;
}

export async function readBoundedJson(response: Response): Promise<unknown> {
  const declaredLength = Number(response.headers.get("content-length"));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_UPSTREAM_BYTES) {
    await response.body?.cancel();
    throw new UpstreamValidationError("The upstream response is too large.");
  }
  if (!response.body) {
    throw new UpstreamValidationError("The upstream response has no body.");
  }

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_UPSTREAM_BYTES) {
        await reader.cancel();
        throw new UpstreamValidationError(
          "The upstream response is too large.",
        );
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  try {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch {
    throw new UpstreamValidationError("The upstream response is not JSON.");
  }
}
