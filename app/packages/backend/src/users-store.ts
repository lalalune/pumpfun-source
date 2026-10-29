/**
 * In-memory user store seeded from a small JSON file.
 * All data is deterministic and read-only at runtime. The rows are a complete
 * local account snapshot, not a statement about accounts in upstream services.
 */
import seedData from './users-seed.json' with { type: 'json' };

/**
 * A user row conforming to the contract schema with additionalProperties: false.
 * Required fields: address, username, profile_image, bio, followers, following, x_username.
 * All other fields are optional per the contract.
 */
export interface User {
  address: string;
  userId?: string;
  username: string | null;
  profile_image: string | null;
  header_image_url?: string | null;
  avatar_decoration?: string | null;
  resolved_avatar_decoration?: string | null;
  kind?: 'person' | 'group';
  member_count?: number;
  group_badges?: GroupBadge[];
  bio: string | null;
  followers: number;
  following: number;
  last_username_update_timestamp?: number | null;
  x_username: string | null;
  wallet_label?: string;
  is_pump_user?: boolean;
  is_banned?: boolean;
  canonical_svm_wallet?: string;
  canonical_evm_wallet?: string;
  last_active_at?: string | null;
}

export interface GroupBadge {
  group_id: string;
  username: string;
  profile_image_url: string | null;
  role: string;
}

export interface UserOverview {
  address: string;
  profile: User | null;
  isPumpUser: boolean;
  counts: {
    followers: number | null;
    following: number | null;
  };
  verified: boolean | null;
  achievementBadgeIds: string[] | null;
  banned: boolean | null;
  createdCoinsCount: number | null;
  degraded: string[];
}

export interface UserSearchOptions {
  searchTerm?: string;
  sort?: string;
  order?: string;
  offset?: number;
  limit?: number;
  includeLabelledWallets?: boolean;
}

/** Validated seed users. */
const users: User[] = seedData as User[];

/**
 * The seed is HAND-AUTHORED SYNTHETIC DATA, not captured production traffic.
 *
 * app/AGENTS.md forbids fabricated domain responses, so this dataset is labelled
 * everywhere it surfaces: this constant, the X-Reconstruction-Data-Source response
 * header set by users-routes.ts, and NATIVE-USERS.md. Nothing here is evidence of
 * real pump.fun users, and no claim of API qualification rests on it.
 */
export const SYNTHETIC_SEED: readonly User[] = users;
export const DATA_SOURCE = 'synthetic-seed-play' as const;

/** Index by address for O(1) lookup. */
const byAddress = new Map<string, User>(users.map(u => [u.address, u]));

/** Index by userId for O(1) lookup. */
const byUserId = new Map<string, User>(
  users.filter(u => u.userId !== undefined).map(u => [u.userId!, u])
);

/** Index by (lowercased) username for existence checks. */
const byUsername = new Map<string, User>(
  users.filter(u => u.username !== null).map(u => [u.username!.toLowerCase(), u])
);

/**
 * Valid sort keys. The contract does not constrain `sort` to an enum,
 * so we support the fields that make sense for ordering. Unrecognized
 * sort values fall back to insertion order (documented assumption).
 */
type SortKey = 'followers' | 'following' | 'address' | 'username';
const SORT_KEYS = new Set<string>(['followers', 'following', 'address', 'username']);

function comparePrimitive(a: string | number | null, b: string | number | null, order: 'asc' | 'desc'): number {
  // nulls sort last regardless of direction
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  let cmp: number;
  if (typeof a === 'string' && typeof b === 'string') {
    cmp = a.localeCompare(b);
  } else {
    cmp = (a as number) - (b as number);
  }
  return order === 'desc' ? -cmp : cmp;
}

/**
 * Decode a canonical base58 address to its byte width, including leading zeroes.
 * Same decoder as frontend auth/public-wallet; no curve or ownership claim.
 */
function isWalletAddress(value: string): boolean {
  if (value.length < 32 || value.length > 44) return false;
  const alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  const bytes = [0];
  for (const character of value) {
    let carry = alphabet.indexOf(character);
    if (carry < 0) return false;
    for (let i = 0; i < bytes.length; i++) {
      carry += bytes[i] * 58;
      bytes[i] = carry & 255;
      carry >>= 8;
    }
    while (carry) {
      bytes.push(carry & 255);
      carry >>= 8;
    }
  }
  let leading = 0;
  while (value[leading] === '1') leading++;
  return (bytes.length === 1 && bytes[0] === 0 ? 0 : bytes.length) + leading === 32;
}

const GROUP_BADGE_FIELDS = new Set(['group_id', 'username', 'profile_image_url', 'role']);

/** Keep local group metadata within the declared read-response shape. */
function assertGroupMetadata(user: User): void {
  if (user.member_count !== undefined &&
      (typeof user.member_count !== 'number' || !Number.isFinite(user.member_count)))
    throw new TypeError('Invalid user member_count');
  if (user.group_badges === undefined) return;
  if (!Array.isArray(user.group_badges)) throw new TypeError('Invalid user group_badges');
  for (const badge of user.group_badges) {
    if (!badge || typeof badge !== 'object' || Array.isArray(badge) ||
        [...GROUP_BADGE_FIELDS].some((field) => !Object.hasOwn(badge, field)) ||
        Object.keys(badge).some((field) => !GROUP_BADGE_FIELDS.has(field)) ||
        typeof badge.group_id !== 'string' || typeof badge.username !== 'string' ||
        (badge.profile_image_url !== null && typeof badge.profile_image_url !== 'string') ||
        typeof badge.role !== 'string')
      throw new TypeError('Invalid user group_badges');
  }
}

export class UserStore {
  private users: User[];
  private byAddress: Map<string, User>;
  private byUserId: Map<string, User>;
  private byUsername: Map<string, User>;
  private verifiedUsers: Set<string>;

  constructor(seed?: User[], verifiedIds?: string[] | Set<string>) {
    this.users = structuredClone(seed ?? users);
    const identities = new Set<string>();
    for (const user of this.users) {
      assertGroupMetadata(user);
      for (const id of new Set([user.address, user.userId].filter((id): id is string => typeof id === 'string' && id !== ''))) {
        if (identities.has(id)) throw new TypeError('Duplicate or ambiguous user identity');
        identities.add(id);
      }
    }
    this.byAddress = new Map(this.users.filter(u => u.address !== '').map(u => [u.address, u]));
    this.byUserId = new Map(
      this.users.filter(u => u.userId !== undefined && u.userId !== '').map(u => [u.userId!, u])
    );
    this.byUsername = new Map(
      this.users.filter(u => u.username !== null && u.username !== '').map(u => [u.username!.toLowerCase(), u])
    );
    if (verifiedIds) {
      this.verifiedUsers = new Set(verifiedIds);
    } else {
      // Default verified users from the seed.
      // Alice (user-001 / 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU) is verified.
      this.verifiedUsers = new Set([
        '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
        'user-001',
      ]);
    }
  }

  /** List users with optional sort, order, offset and limit. */
  list(opts: { sort?: string; order?: string; offset?: number; limit?: number }): User[] {
    let result = [...this.users];

    // Sort if a recognized key is provided; otherwise keep insertion order.
    if (opts.sort && SORT_KEYS.has(opts.sort)) {
      const key = opts.sort as SortKey;
      const order: 'asc' | 'desc' = opts.order === 'desc' ? 'desc' : 'asc';
      result.sort((a, b) => comparePrimitive(
        a[key] as string | number | null,
        b[key] as string | number | null,
        order,
      ));
    }

    const offset = opts.offset ?? 0;
    const limit = opts.limit ?? result.length;
    return structuredClone(result.slice(offset, offset + limit));
  }

  /** Search users with query filters, sorting, and pagination. */
  search(opts: UserSearchOptions): User[] {
    if (
      opts.includeLabelledWallets !== undefined &&
      typeof opts.includeLabelledWallets !== 'boolean'
    )
      throw new TypeError('includeLabelledWallets must be a boolean');
    let result = [...this.users];

    // Filter by includeLabelledWallets (defaults to false).
    if (!opts.includeLabelledWallets) {
      result = result.filter(u => !u.wallet_label || u.wallet_label.trim() === '');
    }

    // Filter by searchTerm if provided.
    if (opts.searchTerm && opts.searchTerm.trim() !== '') {
      const term = opts.searchTerm.trim().toLowerCase();
      result = result.filter(u => {
        if (u.username && u.username.toLowerCase().includes(term)) return true;
        if (u.address.toLowerCase().includes(term)) return true;
        if (u.userId && u.userId.toLowerCase().includes(term)) return true;
        if (u.x_username && u.x_username.toLowerCase().includes(term)) return true;
        if (u.wallet_label && u.wallet_label.toLowerCase().includes(term)) return true;
        return false;
      });
    }

    // Sort if a recognized key is provided; otherwise keep insertion order.
    if (opts.sort && SORT_KEYS.has(opts.sort)) {
      const key = opts.sort as SortKey;
      const order: 'asc' | 'desc' = opts.order === 'desc' ? 'desc' : 'asc';
      result.sort((a, b) => comparePrimitive(
        a[key] as string | number | null,
        b[key] as string | number | null,
        order,
      ));
    }

    const offset = opts.offset ?? 0;
    const limit = opts.limit ?? result.length;
    return structuredClone(result.slice(offset, offset + limit));
  }

  /** Check whether a user is verified (by address or userId). Returns false for unknown ids. */
  isVerified(id: string): boolean {
    const user = this.getById(id);
    if (!user) return false;
    return (
      this.verifiedUsers.has(id) ||
      this.verifiedUsers.has(user.address) ||
      (user.userId !== undefined && user.userId !== '' && this.verifiedUsers.has(user.userId))
    );
  }

  /** Batch-check verified status for a list of ids. Returns record mapping id to boolean. */
  batchVerified(ids: string[]): Record<string, boolean> {
    // Define own data properties, including names such as "__proto__". Assignment
    // to a plain object would silently omit that otherwise valid requested key.
    return Object.fromEntries(ids.map(id => [id, this.isVerified(id)]));
  }

  /** Get the local account overview; an absent wallet has a null profile. */
  getOverview(id: string): UserOverview | undefined {
    const user = this.getById(id);
    if (!user) {
      if (!isWalletAddress(id)) return undefined;
      return {
        address: id,
        profile: null,
        isPumpUser: false,
        counts: { followers: null, following: null },
        verified: false,
        achievementBadgeIds: [],
        banned: null,
        createdCoinsCount: null,
        degraded: ['counts', 'banned', 'created_coins'],
      };
    }
    return {
      address: id,
      profile: user,
      // The overview contract defines this as profile !== null, not the row flag.
      isPumpUser: true,
      counts: {
        followers: user.followers,
        following: user.following,
      },
      verified: this.isVerified(id),
      achievementBadgeIds: [],
      banned: user.is_banned ?? false,
      createdCoinsCount: 0,
      degraded: [],
    };
  }

  /** Get a single user by wallet address OR userId. Returns undefined for misses. */
  getById(id: string): User | undefined {
    const user = this.byAddress.get(id) ?? this.byUserId.get(id);
    return user === undefined ? undefined : structuredClone(user);
  }

  /** Batch-fetch users by their wallet addresses. Missing entries are omitted. */
  batch(addresses: string[]): User[] {
    const result: User[] = [];
    for (const addr of addresses) {
      const u = this.byAddress.get(addr);
      if (u) result.push(structuredClone(u));
    }
    return result;
  }

  /** Check whether a username is taken (case-insensitive). */
  usernameExists(username: string): boolean {
    return this.byUsername.has(username.toLowerCase());
  }
}

/** Singleton store for the application. */
export const defaultStore = new UserStore();
