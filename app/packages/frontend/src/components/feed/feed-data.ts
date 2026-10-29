import type { QuotePreviewData } from "../../../../../reconstruction/quote-preview/model.mjs";
export const LOCAL_FEED_DATA_SOURCE = "synthetic-seed-play" as const;
export const POSTS_SEED_SHA256 =
  "f4d12a7812b07be6dcef4b966430a086cba9e867ff89de669a95a74bdd73d705";
export const USERS_SEED_SHA256 =
  "56259663a146236df2f0e6e1d931df7cc2dda4d39ed7a090c18505434155b20d";

type UnknownRecord = Record<string, unknown>;

export type LocalFeedPost = {
  id: string;
  author: {
    address: string;
    userId?: string;
    name: string;
    missing: boolean;
  };
  content: string | null;
  timestamp: string;
  timestampLabel: string;
  likes: number;
  reposts: number;
  replies: number;
  quotes: number;
  hasMedia: boolean;
  dataSource: typeof LOCAL_FEED_DATA_SOURCE;
  quotePreview?: QuotePreviewData;
};

export type LocalFeedDataset = {
  dataSource: typeof LOCAL_FEED_DATA_SOURCE;
  posts: LocalFeedPost[];
  excluded: {
    replies: number;
    deleted: number;
    hidden: number;
    nonRoot: number;
  };
};

export class FeedDataError extends Error {
  override name = "FeedDataError";
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeString(
  record: UnknownRecord,
  field: string,
  {
    nullable = false,
    allowEmpty = false,
  }: { nullable?: boolean; allowEmpty?: boolean } = {},
): string | null {
  const value = record[field];
  if (nullable && value === null) return null;
  if (
    typeof value !== "string" ||
    (!allowEmpty && value.length === 0) ||
    /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value)
  ) {
    throw new FeedDataError(
      `Local feed ${field} must be ${nullable ? "null or " : ""}a non-empty safe string`,
    );
  }
  return value;
}

function optionalSafeString(
  record: UnknownRecord,
  field: string,
): string | null | undefined {
  const value = record[field];
  if (value === undefined) return undefined;
  return safeString(record, field, { nullable: true });
}

function requiredBoolean(record: UnknownRecord, field: string): boolean {
  const value = record[field];
  if (typeof value !== "boolean") {
    throw new FeedDataError(`Local feed ${field} must be a boolean`);
  }
  return value;
}

function optionalBoolean(record: UnknownRecord, field: string): boolean {
  const value = record[field];
  if (value === undefined) return false;
  if (typeof value !== "boolean") {
    throw new FeedDataError(
      `Local feed ${field} must be a boolean when present`,
    );
  }
  return value;
}

function counter(record: UnknownRecord, field: string): number {
  const value = record[field];
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    throw new FeedDataError(
      `Local feed ${field} must be a non-negative safe integer`,
    );
  }
  return value;
}

function parseTimestamp(value: string, field: string): number {
  const timestamp = Date.parse(value);
  const iso =
    /^(\d{4}-\d{2}-\d{2})T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/u.exec(
      value,
    );
  const calendar = iso ? new Date(`${iso[1]}T00:00:00Z`) : null;
  if (
    !Number.isFinite(timestamp) ||
    !iso ||
    !calendar ||
    !Number.isFinite(calendar.getTime()) ||
    calendar.toISOString().slice(0, 10) !== iso[1]
  ) {
    throw new FeedDataError(`Local feed ${field} must be an ISO timestamp`);
  }
  return timestamp;
}

function formatTimestamp(timestamp: number): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(timestamp);
}

function mediaPresence(record: UnknownRecord): boolean {
  const value = optionalSafeString(record, "mediaUrl");
  if (value === undefined || value === null) return false;
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new FeedDataError("Local feed mediaUrl must be an absolute URL");
  }
  if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
    throw new FeedDataError(
      "Local feed mediaUrl uses an unsupported URL scheme",
    );
  }
  return true;
}

type ValidatedUser = {
  address: string;
  userId?: string;
  username: string | null;
};

function validateUsers(input: unknown): Map<string, ValidatedUser> {
  if (!Array.isArray(input)) {
    throw new FeedDataError("Local feed users must be an array");
  }
  const users = new Map<string, ValidatedUser>();
  const addresses = new Set<string>();

  input.forEach((value, index) => {
    if (!isRecord(value)) {
      throw new FeedDataError(`Local feed user ${index} must be an object`);
    }
    const address = safeString(value, "address", {
      allowEmpty: true,
    }) as string;
    const userIdValue = value.userId;
    const userId =
      userIdValue === undefined
        ? undefined
        : (safeString(value, "userId") as string);
    const username = optionalSafeString(value, "username") ?? null;

    if (!address && !userId?.trim()) {
      throw new FeedDataError(
        `Local feed user ${index} requires an address or non-empty user id`,
      );
    }

    if (address && addresses.has(address)) {
      throw new FeedDataError(`Local feed user ${index} repeats an address`);
    }
    if (address) addresses.add(address);
    const keys = [...(address ? [address] : []), ...(userId ? [userId] : [])];
    for (const key of keys) {
      if (users.has(key)) {
        throw new FeedDataError(`Local feed user ${index} repeats an identity`);
      }
    }
    const user = { address, userId, username };
    keys.forEach((key) => users.set(key, user));
  });
  return users;
}

function displayName(user: ValidatedUser | undefined): string {
  if (!user) return "Unknown local author";
  return (
    user.username?.trim() ||
    (user.address
      ? `${user.address.slice(0, 6)}…${user.address.slice(-4)}`
      : "Unnamed local account")
  );
}

export function validateLocalFeed(
  postsInput: unknown,
  usersInput: unknown,
  { includeQuotes = false }: { includeQuotes?: boolean } = {},
): LocalFeedDataset {
  if (typeof includeQuotes !== "boolean")
    throw new FeedDataError("Local quote projection must be boolean");
  if (!Array.isArray(postsInput)) {
    throw new FeedDataError("Local feed posts must be an array");
  }
  const users = validateUsers(usersInput);
  const seenPostIds = new Set<string>();
  const excluded = { replies: 0, deleted: 0, hidden: 0, nonRoot: 0 };
  const posts: Array<
    LocalFeedPost & { timestampMs: number; quoteTargetId?: string | null }
  > = [];
  const quoteTargets = new Map<
    string,
    {
      authorId: string;
      content: string | null;
      deleted: boolean;
      hidden: boolean;
    }
  >();

  postsInput.forEach((value, index) => {
    if (!isRecord(value)) {
      throw new FeedDataError(`Local feed post ${index} must be an object`);
    }
    const id = safeString(value, "postId") as string;
    if (seenPostIds.has(id)) {
      throw new FeedDataError(
        `Local feed post ${index} repeats a post identity`,
      );
    }
    seenPostIds.add(id);

    const authorId = safeString(value, "authorId") as string;
    const kind = value.kind;
    if (
      kind !== "root" &&
      kind !== "reply" &&
      kind !== "quote" &&
      kind !== "repost" &&
      kind !== null
    ) {
      throw new FeedDataError(
        `Local feed post ${index} has an unsupported kind`,
      );
    }
    const content = safeString(value, "content", {
      nullable: true,
      allowEmpty: true,
    });
    const timestamp = safeString(value, "createdAt", { nullable: true });
    const parentPostId = optionalSafeString(value, "parentPostId") ?? null;
    const rootPostId = optionalSafeString(value, "rootPostId") ?? null;
    const deleted = requiredBoolean(value, "deleted");
    const hidden = optionalBoolean(value, "hidden");
    const likes = counter(value, "likeCount");
    const replies = counter(value, "replyCount");
    const reposts = counter(value, "repostCount");
    const quotes = counter(value, "quoteCount");
    const hasMedia = mediaPresence(value);
    if (includeQuotes)
      quoteTargets.set(id, { authorId, content, deleted, hidden });

    if (deleted) {
      excluded.deleted += 1;
      return;
    }
    if (hidden) {
      excluded.hidden += 1;
      return;
    }
    if (kind === "reply" || parentPostId !== null || rootPostId !== null) {
      excluded.replies += 1;
      return;
    }
    if (kind !== "root" && !(includeQuotes && kind === "quote")) {
      excluded.nonRoot += 1;
      return;
    }
    if (timestamp === null) {
      throw new FeedDataError(
        `Local feed post ${index} is missing its timestamp`,
      );
    }
    const timestampMs = parseTimestamp(timestamp, `post ${index} createdAt`);
    const author = users.get(authorId);
    posts.push({
      id,
      author: {
        address: author?.address ?? authorId,
        ...(author?.userId ? { userId: author.userId } : {}),
        name: displayName(author),
        missing: !author,
      },
      content,
      timestamp,
      timestampLabel: formatTimestamp(timestampMs),
      likes,
      reposts,
      replies,
      quotes,
      hasMedia,
      dataSource: LOCAL_FEED_DATA_SOURCE,
      timestampMs,
      ...(kind === "quote"
        ? { quoteTargetId: optionalSafeString(value, "quotedPostId") ?? null }
        : {}),
    });
  });

  posts.sort(
    (left, right) =>
      right.timestampMs - left.timestampMs || left.id.localeCompare(right.id),
  );

  return {
    dataSource: LOCAL_FEED_DATA_SOURCE,
    posts: posts.map(
      ({ timestampMs: _timestampMs, quoteTargetId, ...post }) => {
        if (quoteTargetId === undefined) return post;
        // New local host join. It does not assert the original API's coordinator
        // or visibility policy; hidden/deleted/unresolved target text is withheld.
        const target =
          quoteTargetId === null ? undefined : quoteTargets.get(quoteTargetId);
        const author = target ? users.get(target.authorId) : undefined;
        const quotePreview: QuotePreviewData =
          !target || target.deleted || target.hidden
            ? { deleted: true }
            : {
                deleted: false,
                ...(author?.username !== null && author?.username !== undefined
                  ? { authorName: author.username }
                  : {}),
                ...(author?.address ? { authorAddress: author.address } : {}),
                ...(target.content ? { text: target.content } : {}),
              };
        return { ...post, quotePreview };
      },
    ),
    excluded,
  };
}
