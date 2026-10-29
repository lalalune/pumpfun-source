/**
 * In-memory posts store seeded from a JSON file.
 * All data is deterministic and read-only at runtime.
 */
import seedData from './posts-seed.json' with { type: 'json' };
import { User, UserStore, defaultStore, DATA_SOURCE } from './users-store.js';

export { DATA_SOURCE };

export interface RawMention {
  userId: string;
  username: string;
  walletAddress: string | null;
}

export interface RawPost {
  postId: string;
  authorId: string;
  kind: 'root' | 'reply' | 'quote' | 'repost' | null;
  content: string | null;
  mediaUrl: string | null;
  createdAt: string | null;
  parentPostId: string | null;
  rootPostId: string | null;
  quotedPostId: string | null;
  repostedPostId: string | null;
  likeCount: number;
  replyCount: number;
  repostCount: number;
  quoteCount: number;
  mentions: RawMention[];
  deleted: boolean;
  hidden?: boolean;
  likers?: string[];
  reposters?: string[];
}

export interface AuthorProfile {
  userId: string;
  username: string;
  bio: string;
  profileImageUrl: string;
  headerImageUrl: string;
  followerCount: number;
  followingCount: number;
  createdAt: string | null;
  updatedAt: string | null;
  walletAddress: string | null;
  socials: Array<{
    provider: string;
    username: string;
    linkedAt: string | null;
  }>;
  isVerified: boolean;
  verifiedBadgeVisible: boolean;
  resolvedAvatarDecoration?: string | null;
  kind: 'PERSON' | 'GROUP';
  memberCount: number;
  membershipPolicy: 'INVITE' | null;
  groupBadges: Array<{
    groupId: string;
    username: string;
    profileImageUrl: string | null;
    role: string;
  }>;
  generatedMedia: {
    pnlLoop: {
      uid: string;
      durationSeconds: number;
    };
    replayIntro?: {
      uid: string;
      durationSeconds: number;
      fireAt: number;
    };
  } | null;
  isPumpUser?: boolean;
}

export interface UserProfile extends AuthorProfile {
  viewerFollows?: boolean;
}

export interface Post {
  postId: string;
  kind: 'root' | 'reply' | 'quote' | 'repost' | null;
  author: AuthorProfile | null;
  content: string | null;
  mediaUrl: string | null;
  createdAt: string | null;
  parentPostId: string | null;
  rootPostId: string | null;
  quotedPostId: string | null;
  repostedPostId: string | null;
  likeCount: number;
  replyCount: number;
  repostCount: number;
  quoteCount: number;
  mentions: RawMention[];
  hasLiked: boolean | null;
  hasReposted: boolean | null;
  deleted: boolean;
  parent: Post | null;
  quoted: Post | null;
  reposted: Post | null;
}

export const SYNTHETIC_POSTS_SEED: readonly RawPost[] = seedData as RawPost[];

export function userToProfile(user: User, isVerified: boolean): UserProfile {
  return {
    userId: user.userId ?? user.address,
    username: user.username ?? user.address.slice(0, 8),
    bio: user.bio ?? '',
    profileImageUrl: user.profile_image ?? '',
    headerImageUrl: user.header_image_url ?? '',
    followerCount: user.followers,
    followingCount: user.following,
    createdAt: null,
    updatedAt: null,
    walletAddress: user.canonical_svm_wallet || user.address || null,
    socials: user.x_username ? [{ provider: 'twitter', username: user.x_username, linkedAt: null }] : [],
    isVerified,
    verifiedBadgeVisible: isVerified,
    resolvedAvatarDecoration: user.resolved_avatar_decoration ?? null,
    kind: user.kind === 'group' ? 'GROUP' : 'PERSON',
    memberCount: user.member_count ?? 0,
    membershipPolicy: null,
    groupBadges: (user.group_badges ?? []).map(b => ({
      groupId: b.group_id,
      username: b.username,
      profileImageUrl: b.profile_image_url ?? null,
      role: b.role,
    })),
    generatedMedia: null,
    isPumpUser: user.is_pump_user ?? true,
  };
}

export function encodeCursor(item: { createdAt: string | null; postId: string }): string {
  const payload = JSON.stringify([item.createdAt ?? '', item.postId]);
  return Buffer.from(payload, 'utf8').toString('base64url');
}

export function decodeCursor(cursor: unknown): { createdAt: string; postId: string } | null {
  try {
    // Buffer's base64 decoder silently ignores junk and accepts alternate
    // encodings. Require the unchanged encoder's alphabet and trailing bits.
    if (typeof cursor !== 'string' || !/^[A-Za-z0-9_-]+$/.test(cursor)) return null;
    const bytes = Buffer.from(cursor, 'base64url');
    if (bytes.toString('base64url') !== cursor) return null;
    const raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed) && parsed.length === 2 && typeof parsed[0] === 'string' && typeof parsed[1] === 'string') {
      // Preserve the null-time sentinel and all date representations understood
      // by the existing comparator. NaN would otherwise silently empty a page.
      if (parsed[0] !== '' && !Number.isFinite(new Date(parsed[0]).getTime())) return null;
      if (/[\u0000-\u001f\u007f]/.test(parsed[1])) return null;
      encodeURIComponent(parsed[1]); // Reject lone surrogates before comparison.
      return { createdAt: parsed[0], postId: parsed[1] };
    }
    return null;
  } catch {
    return null;
  }
}

// Keep locale ordering, but break collation equivalence with the exact ID.
// Keyset pagination needs a total order over distinct identities.
function comparePostIds(a: string, b: string): number {
  return a.localeCompare(b) || (a === b ? 0 : a < b ? -1 : 1);
}

function comparePostsNewestFirst(a: RawPost, b: RawPost): number {
  const timeA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
  const timeB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
  if (timeA !== timeB) {
    return timeB - timeA; // newest first
  }
  return comparePostIds(b.postId, a.postId);
}

export class PostStore {
  private posts: RawPost[];
  private byPostId: Map<string, RawPost>;
  private userStore: UserStore;

  constructor(seed?: RawPost[], userStore?: UserStore) {
    // The store documents deterministic read-only data: snapshot the seed so
    // caller-owned rows (and the shared default seed) cannot corrupt later reads.
    this.posts = structuredClone(seed ?? (seedData as RawPost[]));
    if (new Set(this.posts.map(p => p.postId)).size !== this.posts.length) throw new TypeError('Duplicate post identity');
    this.byPostId = new Map(this.posts.map(p => [p.postId, p]));
    this.userStore = userStore ?? defaultStore;
  }

  /** Hydrate a raw post to conform to Shared_47a8d5353d95. depth > 0 omits nested embeds. */
  hydrate(raw: RawPost, depth = 0): Post {
    if (raw.deleted) {
      // Deleted tombstone
      return {
        postId: raw.postId,
        kind: raw.kind,
        author: null,
        content: null,
        mediaUrl: null,
        createdAt: raw.createdAt,
        parentPostId: raw.parentPostId,
        rootPostId: raw.rootPostId,
        quotedPostId: raw.quotedPostId,
        repostedPostId: raw.repostedPostId,
        likeCount: raw.likeCount,
        replyCount: raw.replyCount,
        repostCount: raw.repostCount,
        quoteCount: raw.quoteCount,
        mentions: [],
        hasLiked: raw.kind === 'repost' ? false : null,
        hasReposted: raw.kind === 'repost' ? false : null,
        deleted: true,
        parent: null,
        quoted: null,
        reposted: null,
      };
    }

    const user = this.userStore.getById(raw.authorId);
    const author = user ? userToProfile(user, this.userStore.isVerified(user.userId ?? user.address)) : null;

    let parent: Post | null = null;
    let quoted: Post | null = null;
    let reposted: Post | null = null;

    if (depth === 0) {
      if (raw.parentPostId) {
        const parentRaw = this.byPostId.get(raw.parentPostId);
        if (parentRaw && !parentRaw.hidden) {
          parent = this.hydrate(parentRaw, depth + 1);
        }
      }

      if (raw.quotedPostId) {
        const quotedRaw = this.byPostId.get(raw.quotedPostId);
        if (quotedRaw && !quotedRaw.deleted && !quotedRaw.hidden) {
          quoted = this.hydrate(quotedRaw, depth + 1);
        }
      }

      if (raw.repostedPostId) {
        const repostedRaw = this.byPostId.get(raw.repostedPostId);
        if (repostedRaw && !repostedRaw.deleted && !repostedRaw.hidden) {
          reposted = this.hydrate(repostedRaw, depth + 1);
        }
      }
    }

    return {
      postId: raw.postId,
      kind: raw.kind,
      author,
      content: raw.content,
      mediaUrl: raw.mediaUrl,
      createdAt: raw.createdAt,
      parentPostId: raw.parentPostId,
      rootPostId: raw.rootPostId,
      quotedPostId: raw.quotedPostId,
      repostedPostId: raw.repostedPostId,
      likeCount: raw.likeCount,
      replyCount: raw.replyCount,
      repostCount: raw.repostCount,
      quoteCount: raw.quoteCount,
      // Clone the mentions array: returning the stored array lets a caller
      // push into (or rewrite) the seed row's mentions for every later read.
      mentions: structuredClone(raw.mentions ?? []),
      hasLiked: raw.kind === 'repost' ? false : null,
      hasReposted: raw.kind === 'repost' ? false : null,
      deleted: false,
      parent,
      quoted,
      reposted,
    };
  }

  /**
   * A post row can be served when it is live. A repost also needs a live target, because the
   * contract's `reposted` embed is "always present on a served repost".
   */
  private isServed(raw: RawPost): boolean {
    if (raw.deleted || raw.hidden) return false;
    if (raw.kind !== 'repost') return true;
    const target = raw.repostedPostId ? this.byPostId.get(raw.repostedPostId) : undefined;
    return target !== undefined && !target.deleted && !target.hidden;
  }

  /**
   * Get a servable post by ID. Returns undefined for unknown, deleted, or hidden posts,
   * and for reposts whose target is unknown, deleted, or hidden.
   */
  getLivePost(postId: string): Post | undefined {
    const raw = this.byPostId.get(postId);
    if (!raw || !this.isServed(raw)) return undefined;
    return this.hydrate(raw);
  }

  /**
   * Batch-fetch posts by ids in requested order.
   * Duplicates collapse, and ids that cannot be served (see isServed) leave no placeholder.
   */
  batch(ids: string[]): Post[] {
    const seen = new Set<string>();
    const result: Post[] = [];

    for (const id of ids) {
      if (seen.has(id)) continue;
      seen.add(id);

      const raw = this.byPostId.get(id);
      if (raw && this.isServed(raw)) {
        result.push(this.hydrate(raw));
      }
    }

    return result;
  }

  /**
   * Keyset-paginated live replies to a post, newest first.
   * Returns undefined if the post is not live.
   */
  getReplies(postId: string, opts: { cursor?: string; limit?: number }): { replies: Post[]; nextCursor: string | null } | undefined {
    const post = this.byPostId.get(postId);
    if (!post || !this.isServed(post)) return undefined;

    let items = this.posts.filter(p => p.parentPostId === postId && !p.deleted && !p.hidden);
    items.sort(comparePostsNewestFirst);

    if (opts.cursor !== undefined) {
      const decoded = decodeCursor(opts.cursor);
      if (!decoded) {
        throw new Error('INVALID_CURSOR');
      }
      const cursorTime = decoded.createdAt ? new Date(decoded.createdAt).getTime() : 0;
      items = items.filter(item => {
        const itemTime = item.createdAt ? new Date(item.createdAt).getTime() : 0;
        if (itemTime < cursorTime) return true;
        if (itemTime === cursorTime) return comparePostIds(item.postId, decoded.postId) < 0;
        return false;
      });
    }

    const limit = opts.limit ?? 50;
    const page = items.slice(0, limit);
    const hasMore = items.length > limit;
    const nextCursor = hasMore && page.length > 0 ? encodeCursor(page[page.length - 1]) : null;

    return {
      replies: page.map(p => this.hydrate(p)),
      nextCursor,
    };
  }

  /**
   * Keyset-paginated live quotes of a post, newest first.
   * Returns undefined if the post is not live.
   */
  getQuotes(postId: string, opts: { cursor?: string; limit?: number }): { quotes: Post[]; nextCursor: string | null } | undefined {
    const post = this.byPostId.get(postId);
    if (!post || !this.isServed(post)) return undefined;

    let items = this.posts.filter(p => p.quotedPostId === postId && p.kind === 'quote' && !p.deleted && !p.hidden);
    items.sort(comparePostsNewestFirst);

    if (opts.cursor !== undefined) {
      const decoded = decodeCursor(opts.cursor);
      if (!decoded) {
        throw new Error('INVALID_CURSOR');
      }
      const cursorTime = decoded.createdAt ? new Date(decoded.createdAt).getTime() : 0;
      items = items.filter(item => {
        const itemTime = item.createdAt ? new Date(item.createdAt).getTime() : 0;
        if (itemTime < cursorTime) return true;
        if (itemTime === cursorTime) return comparePostIds(item.postId, decoded.postId) < 0;
        return false;
      });
    }

    const limit = opts.limit ?? 50;
    const page = items.slice(0, limit);
    const hasMore = items.length > limit;
    const nextCursor = hasMore && page.length > 0 ? encodeCursor(page[page.length - 1]) : null;

    return {
      quotes: page.map(p => this.hydrate(p)),
      nextCursor,
    };
  }

  /**
   * Offset-paginated likers of a post.
   * Returns undefined if the post is not live.
   */
  getLikers(postId: string, opts: { offset?: number; limit?: number }): { likers: UserProfile[]; hasMore: boolean } | undefined {
    const post = this.byPostId.get(postId);
    if (!post || !this.isServed(post)) return undefined;

    const likerIds = (post.likers ?? []).filter(id => this.userStore.getById(id) !== undefined);
    const offset = Math.max(0, opts.offset ?? 0);
    const limit = Math.max(1, opts.limit ?? 50);

    const slice = likerIds.slice(offset, offset + limit);
    const hasMore = offset + limit < likerIds.length;

    const likers: UserProfile[] = [];
    for (const id of slice) {
      const user = this.userStore.getById(id);
      if (user) {
        likers.push(userToProfile(user, this.userStore.isVerified(user.userId ?? user.address)));
      }
    }

    return { likers, hasMore };
  }

  /**
   * Offset-paginated reposters of a post.
   * Returns undefined if the post is not live.
   */
  getReposters(postId: string, opts: { offset?: number; limit?: number }): { reposters: UserProfile[]; hasMore: boolean } | undefined {
    const post = this.byPostId.get(postId);
    if (!post || !this.isServed(post)) return undefined;

    const reposterIds = (post.reposters ?? []).filter(id => this.userStore.getById(id) !== undefined);
    const offset = Math.max(0, opts.offset ?? 0);
    const limit = Math.max(1, opts.limit ?? 50);

    const slice = reposterIds.slice(offset, offset + limit);
    const hasMore = offset + limit < reposterIds.length;

    const reposters: UserProfile[] = [];
    for (const id of slice) {
      const user = this.userStore.getById(id);
      if (user) {
        reposters.push(userToProfile(user, this.userStore.isVerified(user.userId ?? user.address)));
      }
    }

    return { reposters, hasMore };
  }
}

export const defaultPostStore = new PostStore();
