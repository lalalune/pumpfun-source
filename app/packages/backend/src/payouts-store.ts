import { closeSync, constants, fstatSync, openSync, readSync } from "node:fs";

export type PayoutPeriod = "1d" | "1w" | "1m";
export type PayoutStatus =
  | "awaiting_approval"
  | "pending"
  | "signed"
  | "submitted"
  | "confirmed"
  | "failed"
  | "rejected";

/** Local inputs, not a recovered database schema or proof of wallet ownership. */
export interface PayoutOwner {
  userId: string;
  wallets: string[];
  username: string | null;
  profileImageUrl: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  twitterId: string | null;
  walletAddress: string | null;
}
export interface PayoutFact {
  id: string;
  wallet: string;
  amountAtomic: string;
  status: PayoutStatus;
  paidAt: string | null;
}
export interface PayoutsDataset {
  schemaVersion: 1;
  dataSource: "synthetic" | "local-materialized";
  observedAt: string;
  generatedAt: string | null;
  owners: PayoutOwner[];
  payouts: PayoutFact[];
  /** Explicit local [startAt, endAt) cuts; no guessed rolling-month duration. */
  windows: Partial<Record<PayoutPeriod, { startAt: string; endAt: string }>>;
}
export interface PayoutLeaderboardEntry {
  rank: number;
  userId: string | null;
  username: string | null;
  profileImageUrl: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  twitterId: string | null;
  twitterUrl: string | null;
  wallets: string[];
  totalPaidUsdc: number;
  payoutCount: number;
  lastPaidAt: string | null;
  walletAddress: string | null;
}
export interface PayoutLeaderboard {
  entries: PayoutLeaderboardEntry[];
  totalEarners: number;
  generatedAt: string | null;
}
export class UnavailablePayoutWindowError extends Error {}

const periods = ["1d", "1w", "1m"] as const;
const statuses: readonly string[] = [
  "awaiting_approval",
  "pending",
  "signed",
  "submitted",
  "confirmed",
  "failed",
  "rejected",
];
const MAX_FILE_BYTES = 16 * 1024 * 1024;
const MAX_ATOMIC = BigInt(Number.MAX_SAFE_INTEGER);
function invalid(field: string): never {
  throw new TypeError(`Invalid local payouts dataset: ${field}`);
}
function record(value: unknown, keys: readonly string[], field: string) {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    ![Object.prototype, null].includes(Object.getPrototypeOf(value))
  )
    invalid(field);
  const item = value as Record<string, unknown>;
  if (
    Object.keys(item).length !== keys.length ||
    keys.some((key) => !Object.hasOwn(item, key)) ||
    Object.keys(item).some((key) => !keys.includes(key))
  )
    invalid(field);
  return item;
}
function text(value: unknown, field: string): string {
  if (
    typeof value !== "string" ||
    !value.length ||
    value.length > 2048 ||
    /[\u0000-\u001f\u007f]/u.test(value)
  )
    invalid(field);
  return value;
}
function nullableText(value: unknown, field: string): string | null {
  return value === null ? null : text(value, field);
}
function timestamp(value: unknown, field: string): string {
  const result = text(value, field);
  const ms = Date.parse(result);
  if (
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(result) ||
    !Number.isFinite(ms) ||
    new Date(ms).toISOString() !== result
  )
    invalid(field);
  return result;
}
function list(value: unknown, max: number, field: string): unknown[] {
  if (!Array.isArray(value) || value.length > max) invalid(field);
  for (let index = 0; index < value.length; index++) if (!Object.hasOwn(value, index)) invalid(field);
  return value;
}
function compare(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}
function wholeUsdc(atoms: bigint): number {
  if (atoms > MAX_ATOMIC)
    invalid("aggregate amount exceeds local precision bound");
  const value = Number(atoms) / 1_000_000;
  // Refuse a six-decimal amount the JSON number surface cannot round-trip.
  if (BigInt(value.toFixed(6).replace(".", "")) !== atoms)
    invalid("aggregate amount cannot round-trip at six decimals");
  return value;
}

/** Immutable, opt-in read model. No seeded users, live data, sessions or writes. */
export class PayoutsStore {
  readonly dataSource: PayoutsDataset["dataSource"];
  readonly observedAt: string;
  readonly #boards = new Map<string, PayoutLeaderboard>();

  constructor(input: unknown) {
    const data = record(
      input,
      [
        "schemaVersion",
        "dataSource",
        "observedAt",
        "generatedAt",
        "owners",
        "payouts",
        "windows",
      ],
      "root",
    );
    if (
      data.schemaVersion !== 1 ||
      (data.dataSource !== "synthetic" &&
        data.dataSource !== "local-materialized")
    )
      invalid("version/source");
    this.dataSource = data.dataSource;
    this.observedAt = timestamp(data.observedAt, "observedAt");
    const generatedAt =
      data.generatedAt === null
        ? null
        : timestamp(data.generatedAt, "generatedAt");
    if (generatedAt !== null && generatedAt > this.observedAt)
      invalid("future generatedAt");

    const byWallet = new Map<string, PayoutOwner>();
    const userIds = new Set<string>();
    for (const value of list(data.owners, 10_000, "owners")) {
      const row = record(
        value,
        [
          "userId",
          "wallets",
          "username",
          "profileImageUrl",
          "isVerified",
          "verifiedBadgeVisible",
          "twitterId",
          "walletAddress",
        ],
        "owner",
      );
      const userId = text(row.userId, "owner.userId");
      if (userIds.has(userId)) invalid("duplicate owner");
      userIds.add(userId);
      const wallets = list(row.wallets, 200, "owner.wallets").map((wallet) =>
        text(wallet, "owner.wallet"),
      );
      if (!wallets.length || new Set(wallets).size !== wallets.length)
        invalid("owner.wallets");
      if (
        typeof row.isVerified !== "boolean" ||
        typeof row.verifiedBadgeVisible !== "boolean"
      )
        invalid("owner badge");
      const twitterId = nullableText(row.twitterId, "owner.twitterId");
      if (twitterId !== null && !/^[0-9]{1,30}$/.test(twitterId))
        invalid("owner.twitterId");
      const walletAddress = nullableText(
        row.walletAddress,
        "owner.walletAddress",
      );
      if (walletAddress !== null && !wallets.includes(walletAddress))
        invalid("unmapped canonical wallet");
      const owner: PayoutOwner = {
        userId,
        wallets,
        twitterId,
        walletAddress,
        username: nullableText(row.username, "owner.username"),
        profileImageUrl: nullableText(
          row.profileImageUrl,
          "owner.profileImageUrl",
        ),
        isVerified: row.isVerified,
        verifiedBadgeVisible: row.verifiedBadgeVisible,
      };
      for (const wallet of wallets) {
        if (byWallet.has(wallet)) invalid("ambiguous wallet owner");
        byWallet.set(wallet, owner);
      }
    }

    const ids = new Set<string>();
    const facts = list(data.payouts, 100_000, "payouts").map((value) => {
      const row = record(
        value,
        ["id", "wallet", "amountAtomic", "status", "paidAt"],
        "payout",
      );
      const id = text(row.id, "payout.id");
      if (ids.has(id)) invalid("duplicate payout");
      ids.add(id);
      const wallet = text(row.wallet, "payout.wallet");
      if (
        typeof row.amountAtomic !== "string" ||
        !/^[1-9][0-9]{0,15}$/.test(row.amountAtomic)
      )
        invalid("payout.amountAtomic");
      const atoms = BigInt(row.amountAtomic);
      if (atoms > MAX_ATOMIC) invalid("payout.amountAtomic");
      if (typeof row.status !== "string" || !statuses.includes(row.status))
        invalid("payout.status");
      const paidAt =
        row.paidAt === null ? null : timestamp(row.paidAt, "payout.paidAt");
      if (
        (row.status === "confirmed" && paidAt === null) ||
        (paidAt !== null && paidAt > this.observedAt)
      )
        invalid("payout.paidAt");
      return { wallet, atoms, status: row.status, paidAt };
    });

    if (
      !data.windows ||
      typeof data.windows !== "object" ||
      Array.isArray(data.windows)
    )
      invalid("windows");
    const windowKeys = Object.keys(data.windows);
    if (windowKeys.some((key) => !periods.includes(key as PayoutPeriod)))
      invalid("windows");
    const windows = record(data.windows, windowKeys, "windows");
    const cuts = new Map<string, { startAt: string; endAt: string }>();
    for (const period of windowKeys) {
      const cut = record(windows[period], ["startAt", "endAt"], "window");
      const startAt = timestamp(cut.startAt, "window.startAt");
      const endAt = timestamp(cut.endAt, "window.endAt");
      if (startAt >= endAt || endAt > this.observedAt)
        invalid("window interval");
      cuts.set(period, { startAt, endAt });
    }

    for (const period of ["all", ...windowKeys]) {
      const cut = cuts.get(period);
      const grouped = new Map<
        string,
        {
          owner: PayoutOwner | undefined;
          wallets: Set<string>;
          atoms: bigint;
          count: number;
          lastPaidAt: string;
        }
      >();
      for (const fact of facts) {
        if (fact.status !== "confirmed") continue;
        const paidAt = fact.paidAt!;
        if (cut && (paidAt < cut.startAt || paidAt >= cut.endAt)) continue;
        const owner = byWallet.get(fact.wallet);
        // Tagged JSON keys avoid user/wallet delimiter collisions. The exact
        // code-unit tie order is local policy, not an observed upstream rule.
        const key = JSON.stringify(
          owner ? ["user", owner.userId] : ["wallet", fact.wallet],
        );
        let group = grouped.get(key);
        if (!group) {
          group = {
            owner,
            wallets: new Set(),
            atoms: 0n,
            count: 0,
            lastPaidAt: paidAt,
          };
          grouped.set(key, group);
        }
        group.wallets.add(fact.wallet);
        group.atoms += fact.atoms;
        group.count += 1;
        if (paidAt > group.lastPaidAt) group.lastPaidAt = paidAt;
      }
      const ranked = [...grouped].sort(([leftKey, left], [rightKey, right]) =>
        left.atoms > right.atoms
          ? -1
          : left.atoms < right.atoms
            ? 1
            : compare(leftKey, rightKey),
      );
      // Validate every total, including earners beyond the served top-500 cap.
      const entries = ranked.map(
        ([, group], index): PayoutLeaderboardEntry => ({
          rank: index + 1,
          userId: group.owner?.userId ?? null,
          username: group.owner?.username ?? null,
          profileImageUrl: group.owner?.profileImageUrl ?? null,
          isVerified: group.owner?.isVerified ?? false,
          verifiedBadgeVisible: group.owner?.verifiedBadgeVisible ?? true,
          twitterId: group.owner?.twitterId ?? null,
          twitterUrl: group.owner?.twitterId
            ? `https://x.com/i/user/${group.owner.twitterId}`
            : null,
          wallets: [...group.wallets].sort(compare),
          totalPaidUsdc: wholeUsdc(group.atoms),
          payoutCount: group.count,
          lastPaidAt: group.lastPaidAt,
          walletAddress: group.owner?.walletAddress ?? null,
        }),
      );
      this.#boards.set(period, {
        entries: entries.slice(0, 500),
        totalEarners: entries.length,
        generatedAt,
      });
    }
  }

  leaderboard(
    options: { page?: number; pageSize?: number; period?: PayoutPeriod } = {},
  ): PayoutLeaderboard {
    const { page = 0, pageSize = 50, period } = options;
    if (
      !Number.isSafeInteger(page) ||
      page < 0 ||
      !Number.isSafeInteger(pageSize) ||
      pageSize < 1 ||
      pageSize > 200 ||
      (period !== undefined && !periods.includes(period))
    )
      throw new RangeError("Invalid payouts query");
    const board = this.#boards.get(period ?? "all");
    if (!board)
      throw new UnavailablePayoutWindowError("No supplied payout window");
    // Avoid overflowing page*pageSize for a valid but distant page.
    const entries =
      page >= Math.ceil(500 / pageSize)
        ? []
        : board.entries.slice(page * pageSize, (page + 1) * pageSize);
    return {
      ...board,
      entries: entries.map((row) => ({ ...row, wallets: [...row.wallets] })),
    };
  }
}

/** Startup-only, bounded regular-file read. No writes, reloads or network. */
export function loadPayoutsStore(
  path: string | undefined,
): PayoutsStore | undefined {
  if (!path) return undefined;
  const fd = openSync(
    path,
    constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK,
  );
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile() || stat.size > MAX_FILE_BYTES) invalid("file type/size");
    const buffer = Buffer.alloc(MAX_FILE_BYTES + 1);
    let size = 0;
    while (size < buffer.length) {
      const count = readSync(fd, buffer, size, buffer.length - size, null);
      if (count === 0) break;
      size += count;
    }
    if (size > MAX_FILE_BYTES) invalid("file size");
    return new PayoutsStore(
      JSON.parse(
        new TextDecoder("utf-8", { fatal: true }).decode(
          buffer.subarray(0, size),
        ),
      ),
    );
  } finally {
    closeSync(fd);
  }
}
