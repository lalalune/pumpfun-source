/**
 * In-memory follow-graph store seeded from a small JSON file.
 *
 * The contract exposes the follow graph only through counts, pages and searches;
 * the edges themselves are never returned. Rows come from the existing UserStore
 * so a follower and the same user served by GET /users/{id} cannot drift apart.
 *
 * All data is deterministic and read-only at runtime.
 */
import seedData from './following-seed.json' with { type: 'json' };
import { defaultStore, type UserStore, type User } from './users-store.js';

/** One directed follow edge: `follower_id` follows `following_id`. */
export interface FollowEdge {
  follower_id: string;
  following_id: string;
  /** Epoch ms the edge was made. */
  timestamp: number;
}

export interface PageOptions {
  /** `followers` (default) orders by the row's follower count, `recent` by edge age. */
  sort?: 'followers' | 'recent';
  offset?: number;
  limit?: number;
}

/**
 * One row of a followers/following page.
 *
 * This is NOT the /users row: the contract gives it its own shape (no bio, no
 * following count, but a `user_id` alias and the edge `timestamp`), so rows are
 * projected explicitly instead of passing a User through. `mutuals` is omitted
 * on purpose - the contract marks it viewer-relative and present only on
 * signed-in reads, never on the API host.
 */
export interface FollowRow {
  username: string | null;
  profile_image: string | null;
  resolved_avatar_decoration: string | null;
  address: string;
  userId: string;
  user_id: string;
  kind: 'person' | 'group';
  timestamp: number | null;
  followers: number;
}

/** The relationship row returned by GET /following/single/{id}. */
export interface FollowRelationship {
  following_id: string;
  user_id: string;
  timestamp: number | null;
}

export const DATA_SOURCE = 'synthetic-seed-play' as const;

const edges: FollowEdge[] = [...(seedData as FollowEdge[])];

const DEFAULT_LIMIT = 20;

function byUsername(a: User, b: User): number {
  const an = a.username ?? '\uffff';
  const bn = b.username ?? '\uffff';
  if (an !== bn) return an < bn ? -1 : 1;
  const left = a.userId ?? a.address;
  const right = b.userId ?? b.address;
  if (left !== right) return left < right ? -1 : 1;
  return a.address === b.address ? 0 : a.address < b.address ? -1 : 1;
}

/**
 * Relevance rank for a search match: exact username, then prefix, then substring,
 * then address substring. 0 means the row does not match and is dropped.
 */
function relevance(user: User, term: string): number {
  const username = (user.username ?? '').toLowerCase();
  if (username && username === term) return 4;
  if (username.startsWith(term)) return 3;
  if (username.includes(term)) return 2;
  if (user.address.toLowerCase().includes(term)) return 1;
  return 0;
}

export class FollowingStore {
  private readonly users: UserStore;
  private readonly edges: FollowEdge[];

  constructor(userStore: UserStore = defaultStore, seed: FollowEdge[] = edges) {
    this.users = userStore;
    this.edges = structuredClone(seed);
    if (this.edges.some(edge =>
      typeof edge.follower_id !== 'string' || edge.follower_id.length === 0 ||
      typeof edge.following_id !== 'string' || edge.following_id.length === 0)) {
      throw new TypeError('Invalid follow identity');
    }
    if (this.edges.some(edge => !Number.isSafeInteger(edge.timestamp) || edge.timestamp < 0)) throw new TypeError('Invalid follow timestamp');
    const pairs = this.edges.map((edge) => JSON.stringify([edge.follower_id, edge.following_id]));
    if (new Set(pairs).size !== pairs.length) throw new TypeError('Duplicate follow relation');
  }

  /** Number of edges pointing at `userId`. */
  countFollowers(userId: string): number {
    return this.edges.filter((e) => e.following_id === userId).length;
  }

  /** Number of edges leaving `userId`. */
  countFollowing(userId: string): number {
    return this.edges.filter((e) => e.follower_id === userId).length;
  }

  /**
   * One page of the users following `userId`.
   *
   * `followers` (default) puts the most-followed accounts first; `recent` puts the
   * newest edge first. Ties break on username then userId so paging is stable.
   */
  followersOf(userId: string, opts: PageOptions = {}): FollowRow[] {
    const page = this.edges
      .filter((e) => e.following_id === userId)
      .map((e) => ({ edge: e, user: this.users.getById(e.follower_id) }))
      .filter((row): row is { edge: FollowEdge; user: User } => row.user !== undefined);
    return this.page(page, opts);
  }

  /** One page of the users `userId` follows. Same ordering rules as followersOf. */
  followingOf(userId: string, opts: PageOptions = {}): FollowRow[] {
    const page = this.edges
      .filter((e) => e.follower_id === userId)
      .map((e) => ({ edge: e, user: this.users.getById(e.following_id) }))
      .filter((row): row is { edge: FollowEdge; user: User } => row.user !== undefined);
    return this.page(page, opts);
  }

  /** Behaviourally identical to the base list, filtered to matching usernames. */
  searchFollowers(userId: string, term: string): User[] {
    return this.search(this.membersOf('followers', userId), term);
  }

  searchFollowing(userId: string, term: string): User[] {
    return this.search(this.membersOf('following', userId), term);
  }

  /** Every user on one side of the graph, unordered: the search candidate set. */
  private membersOf(side: 'followers' | 'following', userId: string): User[] {
    const rows = this.edges
      .filter((e) => (side === 'followers' ? e.following_id === userId : e.follower_id === userId))
      .map((e) => this.users.getById(side === 'followers' ? e.follower_id : e.following_id))
      .filter((user): user is User => user !== undefined);
    return rows;
  }

  /**
   * The edge from `viewerId` to `targetId`, or null when the viewer does not
   * follow the target.
   */
  relationship(targetId: string, viewerId: string): FollowRelationship | null {
    const edge = this.edges.find(
      (e) => e.follower_id === viewerId && e.following_id === targetId,
    );
    if (!edge) return null;
    return {
      following_id: edge.following_id,
      user_id: edge.follower_id,
      timestamp: edge.timestamp,
    };
  }

  private page(
    rows: Array<{ edge: FollowEdge; user: User }>,
    opts: PageOptions,
  ): FollowRow[] {
    if ((opts.offset !== undefined && (!Number.isSafeInteger(opts.offset) || opts.offset < 0)) ||
        (opts.limit !== undefined && (!Number.isSafeInteger(opts.limit) || opts.limit < 1 || opts.limit > 1000)) ||
        (opts.sort !== undefined && !['followers', 'recent'].includes(opts.sort))) throw new RangeError('Invalid follow page options');
    const sorted = [...rows].sort((a, b) => {
      if ((opts.sort ?? 'followers') === 'recent') {
        if (a.edge.timestamp !== b.edge.timestamp) return b.edge.timestamp - a.edge.timestamp;
        return byUsername(a.user, b.user);
      }
      if (a.user.followers !== b.user.followers) return b.user.followers - a.user.followers;
      return byUsername(a.user, b.user);
    });
    const offset = Math.max(0, opts.offset ?? 0);
    const limit = Math.max(0, opts.limit ?? DEFAULT_LIMIT);
    return sorted.slice(offset, offset + limit).map((row) => toFollowRow(row.edge, row.user));
  }

  private search(users: User[], rawTerm: string): User[] {
    const trimmed = rawTerm.trim();
    if ([...trimmed].length < 2) return [];
    const term = trimmed.toLowerCase();
    return users
      .map((user) => ({ user, score: relevance(user, term) }))
      .filter((row) => row.score > 0)
      .sort((a, b) => (a.score !== b.score ? b.score - a.score : byUsername(a.user, b.user)))
      .map((row) => structuredClone(row.user));
  }
}

function toFollowRow(edge: FollowEdge, user: User): FollowRow {
  return {
    username: user.username,
    profile_image: user.profile_image,
    resolved_avatar_decoration: user.resolved_avatar_decoration ?? null,
    address: user.address,
    userId: user.userId ?? user.address,
    user_id: user.userId ?? user.address,
    kind: user.kind ?? 'person',
    timestamp: edge.timestamp,
    followers: user.followers,
  };
}

export const defaultFollowingStore = new FollowingStore();
