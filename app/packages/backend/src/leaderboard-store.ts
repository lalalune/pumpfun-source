/**
 * In-memory PnL-leaderboard store seeded from a JSON file.
 *
 * Serves GET /v1/pnl-leaderboard. All data is deterministic and read-only at
 * runtime and is hand-authored synthetic seed data, not captured evidence
 * (app/AGENTS.md). Profile fields are hydrated from the shared UserStore so a
 * row's identity stays consistent with /v1/users.
 */
import seedData from './leaderboard-seed.json' with { type: 'json' };
import { UserStore, defaultStore, DATA_SOURCE } from './users-store.js';
import { userToProfile, type UserProfile } from './posts-store.js';

export { DATA_SOURCE };

export type Period = 'daily' | 'weekly' | 'monthly';
export type SortKey = 'realized' | 'unrealized' | 'combined';

const PERIODS: Period[] = ['daily', 'weekly', 'monthly'];
const SORTS: SortKey[] = ['realized', 'unrealized', 'combined'];

/**
 * Documented reconstruction assumption: the contract's `periodType` is the
 * numeric enum 0|1|2|3. The three selectable windows map to 1/2/3; 0 is left
 * for an all-time board that this endpoint's `period` enum cannot request.
 */
const PERIOD_TYPE: Record<Period, 0 | 1 | 2 | 3> = { daily: 1, weekly: 2, monthly: 3 };
const PERIOD_LABEL: Record<Period, string> = { daily: 'Daily', weekly: 'Weekly', monthly: 'Monthly' };
const PERIOD_SECONDS: Record<Period, number> = { daily: 86_400, weekly: 604_800, monthly: 2_592_000 };

/**
 * Fixed window anchor so `windowStartSec` is deterministic across calls and
 * hosts. Chosen as 2025-10-01T00:00:00Z, the date the synthetic seed rows were
 * authored around (their lastRefreshedAtMs values fall in September 2025); the
 * window start snaps the anchor down to the period boundary.
 */
const ANCHOR_SEC = Date.parse('2025-10-01T00:00:00Z') / 1000; // 1_759_276_800

export interface TopPosition {
  mint: string;
  chainId: number;
  symbol: string | null;
  name: string | null;
  imageUri: string | null;
}

/** A seed row before ranking and profile hydration. */
export interface RawLeaderboardEntry {
  userId: string | null;
  walletAddress: string;
  pnlSol: number;
  pnlUsd: number;
  pnlPercent: number;
  realizedPnlSol: number;
  realizedPnlUsd: number;
  unrealizedPnlSol: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
  lastRefreshedAtMs: number;
  positions: TopPosition[];
}

/** A served row: exactly the documented keys for an anonymous read. */
export interface LeaderboardEntryView {
  rank: number;
  pnlSol: number;
  pnlUsd: number;
  pnlPercent: number;
  buySpendSol: number;
  lastRefreshedAtMs: number;
  realizedPnlSol: number;
  realizedPnlUsd: number;
  unrealizedPnlSol: number;
  unrealizedPnlUsd: number;
  positionsCount: number;
  topPositions: TopPosition[];
  walletAddress: string;
  username: string | null;
  profileImage: string | null;
  xUsername: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  userId: string | null;
}

export interface LeaderboardView {
  entries: LeaderboardEntryView[];
  periodType: 0 | 1 | 2 | 3;
  periodLabel: string;
  windowStartSec: number;
}

export interface BoardQuery {
  period: Period;
  sort?: SortKey;
  positionsLimit?: number;
  limit?: number;
}

type RawSeed = Record<Period, RawLeaderboardEntry[]>;

export function isPeriod(value: string | undefined): value is Period {
  return value !== undefined && (PERIODS as string[]).includes(value);
}

export function isSort(value: string | undefined): value is SortKey {
  return value !== undefined && (SORTS as string[]).includes(value);
}

export class LeaderboardStore {
  private boards: RawSeed;
  private userStore: UserStore;

  constructor(seed?: RawSeed, userStore?: UserStore) {
    // The store documents deterministic read-only data: snapshot the seed so
    // caller-owned rows (and the shared default seed) cannot corrupt later reads.
    this.boards = structuredClone(seed ?? (seedData as unknown as RawSeed));
    for (const period of PERIODS) {
      const wallets = this.boards[period].map((entry) => entry.walletAddress);
      if (new Set(wallets).size !== wallets.length) throw new TypeError('Duplicate leaderboard wallet');
    }
    this.userStore = userStore ?? defaultStore;
  }

  private sortValue(entry: RawLeaderboardEntry, sort: SortKey): number {
    if (sort === 'realized') return entry.realizedPnlUsd;
    if (sort === 'unrealized') return entry.unrealizedPnlUsd;
    return entry.pnlUsd;
  }

  /** Top positions icons are capped at 5; 0 means count only; the default is 3. */
  private clampPositionsLimit(positionsLimit: number | undefined): number {
    if (positionsLimit === undefined || !Number.isFinite(positionsLimit)) return 3;
    const truncated = Math.trunc(positionsLimit);
    if (truncated <= 0) return 0;
    return Math.min(5, truncated);
  }

  /** Rows served; default and ceiling 100, never negative. */
  private clampLimit(limit: number | undefined): number {
    if (limit === undefined || !Number.isFinite(limit)) return 100;
    return Math.min(100, Math.max(0, Math.trunc(limit)));
  }

  private windowStartSec(period: Period): number {
    const span = PERIOD_SECONDS[period];
    return Math.floor(ANCHOR_SEC / span) * span;
  }

  private hydrate(userId: string | null) {
    const user = userId ? this.userStore.getById(userId) : undefined;
    const verified = user ? this.userStore.isVerified(userId ?? '') : false;
    return {
      username: user?.username ?? null,
      profileImage: user?.profile_image ?? null,
      xUsername: user?.x_username ?? null,
      isVerified: verified,
      verifiedBadgeVisible: verified,
    };
  }

  private buildRow(entry: RawLeaderboardEntry, rank: number, positionsLimit: number): LeaderboardEntryView {
    const profile = this.hydrate(entry.userId);
    return {
      rank,
      pnlSol: entry.pnlSol,
      pnlUsd: entry.pnlUsd,
      pnlPercent: entry.pnlPercent,
      buySpendSol: entry.buySpendSol,
      lastRefreshedAtMs: entry.lastRefreshedAtMs,
      realizedPnlSol: entry.realizedPnlSol,
      realizedPnlUsd: entry.realizedPnlUsd,
      unrealizedPnlSol: entry.unrealizedPnlSol,
      unrealizedPnlUsd: entry.unrealizedPnlUsd,
      positionsCount: entry.positions.length,
      // Clone each position: returning stored rows lets a caller rewrite a
      // seed row's position for every later read.
      topPositions: entry.positions.slice(0, positionsLimit).map((position) => ({ ...position })),
      walletAddress: entry.walletAddress,
      username: profile.username,
      profileImage: profile.profileImage,
      xUsername: profile.xUsername,
      isVerified: profile.isVerified,
      verifiedBadgeVisible: profile.verifiedBadgeVisible,
      userId: entry.userId,
    };
  }

  /** Local daily-board projection; unresolved/duplicate identities need an explicit adapter policy. */
  public getDailyLeaderProfiles(): UserProfile[] {
    const leaders = this.getBoard({ period: 'daily', sort: 'combined', limit: 10, positionsLimit: 0 });
    const seen = new Set<string>();
    return leaders.entries.map(entry => {
      const user = entry.userId === null ? undefined : this.userStore.getById(entry.userId);
      if (!user) throw new UnavailableLeaderProfilesError();
      const profile = userToProfile(user, this.userStore.isVerified(user.userId ?? user.address));
      if (seen.has(profile.userId)) throw new UnavailableLeaderProfilesError();
      seen.add(profile.userId);
      return profile;
    });
  }

  /**
   * GET /v1/pnl-leaderboard
   * Ranks the period's board by the sort measure (combined by default),
   * descending, tie-broken on walletAddress, then serves up to `limit` rows.
   */
  public getBoard(query: BoardQuery): LeaderboardView {
    if (!isPeriod(query.period) || (query.sort !== undefined && !isSort(query.sort))) throw new RangeError('Invalid leaderboard query');
    const sort: SortKey = query.sort ?? 'combined';
    const positionsLimit = this.clampPositionsLimit(query.positionsLimit);
    const limit = this.clampLimit(query.limit);

    const ranked = [...(this.boards[query.period] ?? [])].sort((a, b) => {
      const delta = this.sortValue(b, sort) - this.sortValue(a, sort);
      if (delta !== 0) return delta;
      return a.walletAddress.localeCompare(b.walletAddress);
    });

    const entries = ranked
      .slice(0, limit)
      .map((entry, index) => this.buildRow(entry, index + 1, positionsLimit));

    return {
      entries,
      periodType: PERIOD_TYPE[query.period],
      periodLabel: PERIOD_LABEL[query.period],
      windowStartSec: this.windowStartSec(query.period),
    };
  }
}

export class UnavailableLeaderProfilesError extends Error {}

export const defaultLeaderboardStore = new LeaderboardStore();
