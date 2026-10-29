/**
 * In-memory competitions store seeded from a JSON file.
 * All data is deterministic and read-only at runtime.
 */
import seedData from './competitions-seed.json' with { type: 'json' };
import { UserStore, defaultStore, DATA_SOURCE } from './users-store.js';

export { DATA_SOURCE };

export interface PrizeTier {
  rankFrom: number;
  rankTo: number;
  amount: string;
}

export interface TopPosition {
  mint: string;
  chainId: number;
  symbol: string | null;
  name: string | null;
  imageUri: string | null;
}

export interface LeaderboardRow {
  entryId: string;
  participantId: string;
  kind: 'group' | 'person';
  rank: number;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
  memberCount: number;
  membersFresh: number;
  struck: boolean;
  lastRefreshedAtMs: number;
  positionsCount: number;
  topPositions: TopPosition[];
  walletAddress: string | null;
  username: string | null;
  profileImageUrl: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  isViewer?: boolean;
  viewerFollows?: boolean | null;
}

export interface WinnerRow extends LeaderboardRow {
  prize: string | null;
}

export interface CompetitionView {
  id: string;
  slug: string;
  kind: 'group' | 'person';
  title: string;
  description: string;
  prizeCopy: string;
  imageUrl: string | null;
  prizes: PrizeTier[];
  registrationOpensAt: string | null;
  registrationClosesAt: string | null;
  startsAt: string | null;
  endsAt: string | null;
  minMembers: number;
  maxMembers: number;
  maxEntries: number;
  entriesCount: number;
  participants: number;
  joinable: boolean;
  phase: 'upcoming' | 'registration' | 'live' | 'ended';
  isFinal: boolean;
  top: LeaderboardRow[];
  winners: WinnerRow[];
}

export interface LeaderboardView {
  builtAtMs: number;
  startSec: number;
  endSec: number;
  totalRanked: number;
  isFinal: boolean;
  entries: LeaderboardRow[];
}

export interface EntryMemberView {
  userId: string;
  walletAddress: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
  fresh: boolean;
  lastRefreshedAtMs: number;
  username: string | null;
  profileImageUrl: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
}

export interface EntryHighlightMemberView {
  userId: string;
  walletAddress: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendUsd: number;
}

export interface EntryHighlightTokenView {
  mint: string;
  chainId: number;
  symbol: string | null;
  name: string | null;
  imageUri: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendUsd: number;
  members: EntryHighlightMemberView[];
}

export interface CompetitionHighlightRowView {
  mint: string;
  chainId: number;
  symbol: string | null;
  name: string | null;
  imageUri: string | null;
  username: string | null;
  profileImageUrl: string | null;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  entryId: string;
  rank: number;
  userId: string;
  walletAddress: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendUsd: number;
}

export interface RawMember {
  userId: string;
  walletAddress?: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
  fresh: boolean;
  lastRefreshedAtMs: number;
}

export interface RawHighlightMember {
  userId: string;
  walletAddress?: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendUsd: number;
}

export interface RawHighlightToken {
  mint: string;
  chainId: number;
  symbol: string | null;
  name: string | null;
  imageUri: string | null;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendUsd: number;
  members: RawHighlightMember[];
}

export interface RawEntry {
  entryId: string;
  participantId: string;
  /** Person's board wallet at competition start; null means no scoring wallet.
   * Omission preserves the legacy profile fallback. Ignored for group entries. */
  walletAddress?: string | null;
  registeredAt: string;
  struck: boolean;
  pnlUsd: number;
  realizedPnlUsd: number;
  unrealizedPnlUsd: number;
  buySpendSol: number;
  membersFresh: number;
  lastRefreshedAtMs: number;
  positions?: TopPosition[];
  members?: RawMember[];
  highlightTokens?: RawHighlightToken[];
}

export interface RawCompetition {
  id: string;
  slug: string;
  kind: 'group' | 'person';
  title: string;
  description: string;
  prizeCopy: string;
  imageUrl: string | null;
  prizes: PrizeTier[];
  registrationOpensAt: string | null;
  registrationClosesAt: string | null;
  startsAt: string | null;
  endsAt: string | null;
  minMembers: number;
  maxMembers: number;
  maxEntries: number;
  phase: 'upcoming' | 'registration' | 'live' | 'ended';
  isFinal: boolean;
  joinable: boolean;
  entries: RawEntry[];
}

interface RankedEntry extends RawEntry {
  rank: number;
}

export class CompetitionStore {
  private competitions: RawCompetition[];
  private byId: Map<string, RawCompetition>;
  private bySlug: Map<string, RawCompetition>;
  private userStore: UserStore;

  constructor(seed?: RawCompetition[], userStore?: UserStore) {
    // The store documents deterministic read-only data: snapshot the seed so
    // caller-owned rows (and the shared default seed) cannot corrupt later reads.
    this.competitions = structuredClone(seed ?? (seedData as unknown as RawCompetition[]));
    if (new Set(this.competitions.map(c => c.id)).size !== this.competitions.length ||
        new Set(this.competitions.map(c => c.slug.toLowerCase())).size !== this.competitions.length) {
      throw new TypeError('Duplicate competition ID or slug');
    }
    const slugOwners = new Map(this.competitions.map(comp => [comp.slug.toLowerCase(), comp]));
    for (const comp of this.competitions) {
      const owner = slugOwners.get(comp.id.toLowerCase());
      if (owner !== undefined && owner !== comp) {
        throw new TypeError('Ambiguous competition ID/slug keyspace');
      }
    }
    // Ranking sorts entries by pnlUsd and the served JSON serializes every
    // entry measure, so a nonfinite measure corrupts both: the comparator
    // returns NaN (a NaN-pnl entry can take rank 1 over a real profit) and
    // JSON turns NaN/Infinity into null. Reject them at construction, like
    // the leaderboard store does for its board measures.
    for (const comp of this.competitions) {
      for (const entry of comp.entries) {
        for (const key of ['pnlUsd', 'realizedPnlUsd', 'unrealizedPnlUsd',
          'buySpendSol', 'membersFresh', 'lastRefreshedAtMs'] as const) {
          if (!Number.isFinite(entry[key])) throw new TypeError(`Competition entry ${key} must be finite`);
        }
        // The nested rows are served and sorted by the same measures: entry
        // members are sorted by pnlUsd in getEntryDetail, highlight tokens
        // are sorted by pnlUsd and their members by pnlUsd in
        // getEntryHighlights, so a nonfinite nested measure corrupts those
        // orderings and serializes to null exactly like a top-level one.
        for (const member of entry.members ?? []) {
          for (const key of ['pnlUsd', 'realizedPnlUsd', 'unrealizedPnlUsd',
            'buySpendSol', 'lastRefreshedAtMs'] as const) {
            if (!Number.isFinite(member[key])) throw new TypeError(`Competition entry member ${key} must be finite`);
          }
        }
        for (const token of entry.highlightTokens ?? []) {
          for (const key of ['pnlUsd', 'realizedPnlUsd', 'unrealizedPnlUsd',
            'buySpendUsd'] as const) {
            if (!Number.isFinite(token[key])) throw new TypeError(`Competition highlight token ${key} must be finite`);
          }
          for (const member of token.members ?? []) {
            for (const key of ['pnlUsd', 'realizedPnlUsd', 'unrealizedPnlUsd',
              'buySpendUsd'] as const) {
              if (!Number.isFinite(member[key])) throw new TypeError(`Competition highlight member ${key} must be finite`);
            }
          }
        }
      }
      // Header numerics are served verbatim in the competition view, and
      // rankTo drives the winners cutoff (Math.max plus a rank filter), so
      // a nonfinite value corrupts both: a NaN count serializes to null and
      // a NaN rankTo empties the winners of an ended competition. Reject
      // them at construction, like the entry measures above.
      for (const key of ['minMembers', 'maxMembers', 'maxEntries'] as const) {
        if (!Number.isFinite(comp[key])) throw new TypeError(`Competition ${key} must be finite`);
      }
      for (const tier of comp.prizes) {
        for (const key of ['rankFrom', 'rankTo'] as const) {
          if (!Number.isFinite(tier[key])) throw new TypeError(`Competition prize ${key} must be finite`);
        }
      }
    }
    this.byId = new Map(this.competitions.map(c => [c.id, c]));
    this.bySlug = new Map(this.competitions.map(c => [c.slug.toLowerCase(), c]));
    this.userStore = userStore ?? defaultStore;
  }

  /**
   * Rank entries in a competition:
   * Eligible entries are ordered by pnlUsd descending, tie-breaking on registeredAt ascending, then entryId.
   * Before the first build, when struck, or with an explicit absent person scoring wallet, rank is 0.
   */
  private rankEntries(comp: RawCompetition): RankedEntry[] {
    // builtAtMs is the maximum refresh time; 0 means no board has been built yet.
    if (!comp.entries.some(entry => entry.lastRefreshedAtMs > 0)) {
      return comp.entries.map(entry => ({ ...entry, rank: 0 }));
    }
    const eligible = (entry: RawEntry) =>
      !entry.struck && !(comp.kind === 'person' && entry.walletAddress === null);
    const unranked: RankedEntry[] = comp.entries.filter(e => !eligible(e)).map(e => ({ ...e, rank: 0 }));
    const nonStruck = comp.entries.filter(eligible);

    nonStruck.sort((a, b) => {
      if (a.pnlUsd !== b.pnlUsd) {
        return b.pnlUsd - a.pnlUsd;
      }
      const timeA = new Date(a.registeredAt).getTime();
      const timeB = new Date(b.registeredAt).getTime();
      if (timeA !== timeB) {
        return timeA - timeB;
      }
      return a.entryId.localeCompare(b.entryId);
    });

    const ranked: RankedEntry[] = nonStruck.map((e, index) => ({ ...e, rank: index + 1 }));
    return [...ranked, ...unranked];
  }

  /**
   * Hydrates a user's profile info from UserStore.
   */
  private hydrateProfile(userId: string) {
    const user = this.userStore.getById(userId);
    const isVerified = user
      ? this.userStore.isVerified(user.userId ?? '') || this.userStore.isVerified(user.address)
      : false;
    return {
      user,
      username: user?.username ?? null,
      profileImageUrl: user?.profile_image ?? null,
      walletAddress: user?.canonical_svm_wallet || user?.address || null,
      isVerified,
      verifiedBadgeVisible: isVerified,
    };
  }

  /**
   * Build LeaderboardRow from a ranked entry.
   */
  private buildLeaderboardRow(
    comp: RawCompetition,
    entry: RankedEntry,
    positionsLimit: number,
  ): LeaderboardRow {
    const profile = this.hydrateProfile(entry.participantId);
    const isPerson = comp.kind === 'person';
    const isFinal = comp.isFinal;

    // Per contract: walletAddress is null for squads, walletless member, and rank-0 before build
    const walletAddress = isPerson && comp.entries.some(row => row.lastRefreshedAtMs > 0)
      ? (entry.walletAddress === undefined ? profile.walletAddress : entry.walletAddress) : null;

    // Per contract: positionsCount and topPositions are 0 / [] for squads and on final boards
    let positionsCount = 0;
    let topPositions: TopPosition[] = [];
    if (isPerson && !isFinal) {
      const positions = entry.positions ?? [];
      positionsCount = positions.length;
      // Clone each position: returning stored rows lets a caller rewrite a
      // seed row's position for every later read.
      topPositions = positions
        .slice(0, Math.max(0, positionsLimit))
        .map((position) => ({ ...position }));
    }

    const memberCount = isPerson ? 1 : (entry.members ? entry.members.length : 0);

    return {
      entryId: entry.entryId,
      participantId: entry.participantId,
      kind: comp.kind,
      rank: entry.rank,
      pnlUsd: entry.pnlUsd,
      realizedPnlUsd: entry.realizedPnlUsd,
      unrealizedPnlUsd: entry.unrealizedPnlUsd,
      buySpendSol: entry.buySpendSol,
      memberCount,
      membersFresh: entry.membersFresh,
      struck: entry.struck,
      lastRefreshedAtMs: entry.lastRefreshedAtMs,
      positionsCount,
      topPositions,
      walletAddress,
      username: profile.username,
      profileImageUrl: profile.profileImageUrl,
      isVerified: profile.isVerified,
      verifiedBadgeVisible: profile.verifiedBadgeVisible,
    };
  }

  /**
   * Convert raw competition into CompetitionView with top and winners populated.
   * `positionsLimit` slices top and winner rows like leaderboard rows (default 3).
   */
  public toCompetitionView(comp: RawCompetition, positionsLimit = 3): CompetitionView {
    const ranked = this.rankEntries(comp);
    const nonStruckRanked = ranked.filter(e => !e.struck && e.rank >= 1);

    // entriesCount: all registered entries, struck included
    const entriesCount = comp.entries.length;
    // participants: non-struck entries
    const participants = comp.entries.filter(entry => !entry.struck).length;

    // top: ranks 1..3 for phase registration or live; [] otherwise
    let top: LeaderboardRow[] = [];
    if (comp.phase === 'registration' || comp.phase === 'live') {
      top = nonStruckRanked
        .slice(0, 3)
        .map(e => this.buildLeaderboardRow(comp, e, positionsLimit));
    }

    // winners: ranks 1..N for phase ended; [] otherwise
    let winners: WinnerRow[] = [];
    if (comp.phase === 'ended') {
      const maxRank = comp.prizes.length > 0
        ? Math.max(...comp.prizes.map(p => p.rankTo))
        : 3;
      winners = nonStruckRanked
        .filter(e => e.rank <= maxRank)
        .map(e => {
          const row = this.buildLeaderboardRow(comp, e, positionsLimit);
          const tier = comp.prizes.find(p => p.rankFrom <= e.rank && e.rank <= p.rankTo);
          return {
            ...row,
            prize: tier ? tier.amount : null,
          };
        });
    }

    return {
      id: comp.id,
      slug: comp.slug,
      kind: comp.kind,
      title: comp.title,
      description: comp.description,
      prizeCopy: comp.prizeCopy,
      imageUrl: comp.imageUrl,
      // Clone the prize tiers: returning the stored array lets a caller
      // push into (or rewrite) the seed row's prizes for every later read.
      prizes: structuredClone(comp.prizes),
      registrationOpensAt: comp.registrationOpensAt,
      registrationClosesAt: comp.registrationClosesAt,
      startsAt: comp.startsAt,
      endsAt: comp.endsAt,
      minMembers: comp.minMembers,
      maxMembers: comp.maxMembers,
      maxEntries: comp.maxEntries,
      entriesCount,
      participants,
      joinable: comp.joinable,
      phase: comp.phase,
      isFinal: comp.isFinal,
      top,
      winners,
    };
  }

  /**
   * GET /v1/competitions
   * Partitions competitions into upcoming, live, and past.
   */
  public listBuckets(): { upcoming: CompetitionView[]; live: CompetitionView[]; past: CompetitionView[] } {
    const upcoming: CompetitionView[] = [];
    const live: CompetitionView[] = [];
    const past: CompetitionView[] = [];

    for (const comp of this.competitions) {
      const view = this.toCompetitionView(comp);
      if (comp.phase === 'upcoming') {
        upcoming.push(view);
      } else if (comp.phase === 'registration' || comp.phase === 'live') {
        live.push(view);
      } else if (comp.phase === 'ended') {
        past.push(view);
      }
    }

    // Deterministic sorting per contract:
    // upcoming: startsAt ascending
    upcoming.sort((a, b) => {
      const timeA = a.startsAt ? new Date(a.startsAt).getTime() : 0;
      const timeB = b.startsAt ? new Date(b.startsAt).getTime() : 0;
      return timeA - timeB;
    });

    // live: endsAt ascending
    live.sort((a, b) => {
      const timeA = a.endsAt ? new Date(a.endsAt).getTime() : 0;
      const timeB = b.endsAt ? new Date(b.endsAt).getTime() : 0;
      return timeA - timeB;
    });

    // past: latest endsAt first, capped at 50
    past.sort((a, b) => {
      const timeA = a.endsAt ? new Date(a.endsAt).getTime() : 0;
      const timeB = b.endsAt ? new Date(b.endsAt).getTime() : 0;
      return timeB - timeA;
    });
    const cappedPast = past.slice(0, 50);

    return { upcoming, live, past: cappedPast };
  }

  /**
   * GET /v1/competitions/:idOrSlug
   */
  public getByIdOrSlug(
    idOrSlug: string,
    opts: { limit?: number; positionsLimit?: number } = {},
  ): { competition: CompetitionView; leaderboard: LeaderboardView } | null {
    const comp = this.byId.get(idOrSlug) ?? this.bySlug.get(idOrSlug.toLowerCase());
    if (!comp) return null;

    const positionsLimit = opts.positionsLimit !== undefined ? opts.positionsLimit : 3;
    const competition = this.toCompetitionView(comp, positionsLimit);
    const ranked = this.rankEntries(comp);
    const nonStruckRanked = ranked.filter(e => !e.struck && e.rank >= 1);

    const limit = opts.limit !== undefined ? opts.limit : 100;

    const entries = nonStruckRanked
      .slice(0, limit)
      .map(e => this.buildLeaderboardRow(comp, e, positionsLimit));

    let builtAtMs = 0;
    for (const e of comp.entries) {
      if (e.lastRefreshedAtMs > builtAtMs) {
        builtAtMs = e.lastRefreshedAtMs;
      }
    }

    const startSec = comp.startsAt ? Math.trunc(new Date(comp.startsAt).getTime() / 1000) : 0;
    // Contract: the last build while live (0 before the first build, like builtAtMs), endsAt once final.
    const endSec = comp.isFinal
      ? (comp.endsAt ? Math.trunc(new Date(comp.endsAt).getTime() / 1000) : 0)
      : Math.trunc(builtAtMs / 1000);

    const leaderboard: LeaderboardView = {
      builtAtMs,
      startSec,
      endSec,
      totalRanked: nonStruckRanked.length,
      isFinal: comp.isFinal,
      entries,
    };

    return { competition, leaderboard };
  }

  /**
   * GET /v1/competitions/:id/entries/:entryId
   */
  public getEntryDetail(
    competitionId: string,
    entryId: string,
  ): { entry: LeaderboardRow; members: EntryMemberView[] } | null {
    const comp = this.byId.get(competitionId) ?? this.bySlug.get(competitionId.toLowerCase());
    if (!comp) return null;

    const ranked = this.rankEntries(comp);
    const target = ranked.find(e => e.entryId === entryId);
    if (!target) return null;

    const entry = this.buildLeaderboardRow(comp, target, 3);
    const members: EntryMemberView[] = [];

    if (comp.kind === 'group') {
      for (const m of target.members ?? []) {
        const profile = this.hydrateProfile(m.userId);
        members.push({
          userId: m.userId,
          walletAddress: m.walletAddress === undefined ? profile.walletAddress : m.walletAddress,
          pnlUsd: m.pnlUsd,
          realizedPnlUsd: m.realizedPnlUsd,
          unrealizedPnlUsd: m.unrealizedPnlUsd,
          buySpendSol: m.buySpendSol,
          fresh: m.fresh,
          lastRefreshedAtMs: m.lastRefreshedAtMs,
          username: profile.username,
          profileImageUrl: profile.profileImageUrl,
          isVerified: profile.isVerified,
          verifiedBadgeVisible: profile.verifiedBadgeVisible,
        });
      }
      members.sort((a, b) => b.pnlUsd - a.pnlUsd);
    } else {
      // For person competitions, the trader is the sole member
      const profile = this.hydrateProfile(target.participantId);
      members.push({
        userId: target.participantId,
        walletAddress: target.walletAddress === undefined ? profile.walletAddress : target.walletAddress,
        pnlUsd: target.pnlUsd,
        realizedPnlUsd: target.realizedPnlUsd,
        unrealizedPnlUsd: target.unrealizedPnlUsd,
        buySpendSol: target.buySpendSol,
        fresh: target.membersFresh > 0,
        lastRefreshedAtMs: target.lastRefreshedAtMs,
        username: profile.username,
        profileImageUrl: profile.profileImageUrl,
        isVerified: profile.isVerified,
        verifiedBadgeVisible: profile.verifiedBadgeVisible,
      });
    }

    return { entry, members };
  }

  /**
   * GET /v1/competitions/:id/entries/:entryId/highlights
   */
  public getEntryHighlights(
    competitionId: string,
    entryId: string,
    opts: { limit?: number } = {},
  ): { entryId: string; tokens: EntryHighlightTokenView[] } | null {
    const comp = this.byId.get(competitionId) ?? this.bySlug.get(competitionId.toLowerCase());
    if (!comp) return null;

    const target = comp.entries.find(e => e.entryId === entryId);
    if (!target) return null;

    // Before the first board build no entry is ranked, so serve no token reel
    // even when the supplied read model still contains retained token rows
    // (matches getCompetitionHighlights, which only reads ranked entries).
    if (!comp.entries.some(entry => entry.lastRefreshedAtMs > 0)) {
      return { entryId, tokens: [] };
    }

    const limit = opts.limit !== undefined ? opts.limit : 10;
    const rawTokens = [...(target.highlightTokens ?? [])];

    rawTokens.sort((a, b) => b.pnlUsd - a.pnlUsd);
    const sliced = rawTokens.slice(0, limit);

    const tokens: EntryHighlightTokenView[] = sliced.map(t => {
      const members: EntryHighlightMemberView[] = (t.members ?? []).map(m => {
        const profile = this.hydrateProfile(m.userId);
        return {
          userId: m.userId,
          walletAddress: m.walletAddress === undefined ? profile.walletAddress : m.walletAddress,
          pnlUsd: m.pnlUsd,
          realizedPnlUsd: m.realizedPnlUsd,
          unrealizedPnlUsd: m.unrealizedPnlUsd,
          buySpendUsd: m.buySpendUsd,
        };
      });

      // Sort member contributions by pnlUsd descending, then userId
      members.sort((a, b) => {
        if (a.pnlUsd !== b.pnlUsd) return b.pnlUsd - a.pnlUsd;
        return a.userId.localeCompare(b.userId);
      });

      return {
        mint: t.mint,
        chainId: t.chainId,
        symbol: t.symbol,
        name: t.name,
        imageUri: t.imageUri,
        pnlUsd: t.pnlUsd,
        realizedPnlUsd: t.realizedPnlUsd,
        unrealizedPnlUsd: t.unrealizedPnlUsd,
        buySpendUsd: t.buySpendUsd,
        members,
      };
    });

    return { entryId, tokens };
  }

  /**
   * GET /v1/competitions/:id/highlights
   */
  public getCompetitionHighlights(
    competitionId: string,
    opts: { limit?: number; perMemberLimit?: number } = {},
  ): { competitionId: string; builtAtMs: number; isFinal: boolean; rows: CompetitionHighlightRowView[] } | null {
    const comp = this.byId.get(competitionId) ?? this.bySlug.get(competitionId.toLowerCase());
    if (!comp) return null;

    const limit = opts.limit !== undefined ? opts.limit : 20;
    const perMemberLimit = opts.perMemberLimit !== undefined ? opts.perMemberLimit : 1;

    const ranked = this.rankEntries(comp);
    const nonStruckRanked = ranked.filter(e => !e.struck && e.rank >= 1);

    const candidateLegs: CompetitionHighlightRowView[] = [];

    for (const entry of nonStruckRanked) {
      for (const token of entry.highlightTokens ?? []) {
        for (const member of token.members ?? []) {
          // Wins only (pnlUsd > 0)
          if (member.pnlUsd > 0) {
            const profile = this.hydrateProfile(member.userId);
            candidateLegs.push({
              mint: token.mint,
              chainId: token.chainId,
              symbol: token.symbol,
              name: token.name,
              imageUri: token.imageUri,
              username: profile.username,
              profileImageUrl: profile.profileImageUrl,
              isVerified: profile.isVerified,
              verifiedBadgeVisible: profile.verifiedBadgeVisible,
              entryId: entry.entryId,
              rank: entry.rank,
              userId: member.userId,
              walletAddress: member.walletAddress === undefined ? profile.walletAddress : member.walletAddress,
              pnlUsd: member.pnlUsd,
              realizedPnlUsd: member.realizedPnlUsd,
              unrealizedPnlUsd: member.unrealizedPnlUsd,
              buySpendUsd: member.buySpendUsd,
            });
          }
        }
      }
    }

    // Per contract: rows are capped per trader before the overall limit.
    const byUser = new Map<string, CompetitionHighlightRowView[]>();
    for (const leg of candidateLegs) {
      const list = byUser.get(leg.userId) ?? [];
      list.push(leg);
      byUser.set(leg.userId, list);
    }

    const filtered: CompetitionHighlightRowView[] = [];
    for (const [, list] of byUser.entries()) {
      list.sort((a, b) => b.pnlUsd - a.pnlUsd);
      filtered.push(...list.slice(0, perMemberLimit));
    }

    // Sort overall by pnlUsd descending
    filtered.sort((a, b) => {
      if (a.pnlUsd !== b.pnlUsd) return b.pnlUsd - a.pnlUsd;
      return a.userId.localeCompare(b.userId);
    });

    const rows = filtered.slice(0, limit);

    let builtAtMs = 0;
    for (const e of comp.entries) {
      if (e.lastRefreshedAtMs > builtAtMs) {
        builtAtMs = e.lastRefreshedAtMs;
      }
    }

    return {
      competitionId: comp.id,
      builtAtMs,
      isFinal: comp.isFinal,
      rows,
    };
  }
}

export const defaultCompetitionStore = new CompetitionStore();
