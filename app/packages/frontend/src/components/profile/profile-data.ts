import { createHash } from "node:crypto";
import {
  LOCAL_FEED_DATA_SOURCE,
  validateLocalFeed,
  type LocalFeedPost,
} from "../feed/feed-data";
import { isValidProfileIdentifier } from "./profile-identifier";
export { isValidProfileIdentifier } from "./profile-identifier";

type UnknownRecord = Record<string, unknown>;

export const LOCAL_PROFILE_DATA_SOURCE = LOCAL_FEED_DATA_SOURCE;

export type LocalProfile = {
  address: string;
  userId?: string;
  displayName: string;
  username: string | null;
  bio: string | null;
  kind: "person" | "group";
  memberCount: number;
  followers: number;
  following: number;
  banned: boolean;
  isPumpUser: boolean;
  xUsername: string | null;
  hasRecordedAvatar: boolean;
  posts: LocalFeedPost[];
  dataSource: typeof LOCAL_PROFILE_DATA_SOURCE;
};

export type LocalProfileDataset = {
  profiles: LocalProfile[];
  dataSource: typeof LOCAL_PROFILE_DATA_SOURCE;
};

export class ProfileDataError extends Error {
  override name = "ProfileDataError";
}

export function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

export function parseProfileSeedBytes(
  label: "posts" | "users" | "following",
  bytes: Uint8Array,
  expectedSha256: string,
): unknown {
  const actualSha256 = sha256(bytes);
  if (actualSha256 !== expectedSha256) {
    throw new ProfileDataError(
      `Local ${label} seed SHA-256 mismatch: expected ${expectedSha256}, received ${actualSha256}`,
    );
  }
  try {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch (error) {
    throw new ProfileDataError(
      `Local ${label} seed is not valid UTF-8 JSON: ${error instanceof Error ? error.message : "unknown parse failure"}`,
    );
  }
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeString(
  record: UnknownRecord,
  field: string,
  options: {
    nullable?: boolean;
    optional?: boolean;
    allowEmpty?: boolean;
  } = {},
): string | null | undefined {
  const value = record[field];
  if (options.optional && value === undefined) return undefined;
  if (options.nullable && value === null) return null;
  if (
    typeof value !== "string" ||
    (!options.allowEmpty && value.length === 0) ||
    /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/u.test(value)
  ) {
    throw new ProfileDataError(
      `Local profile ${field} has an invalid string value`,
    );
  }
  return value;
}

function nonnegativeInteger(
  record: UnknownRecord,
  field: string,
  { optional = false }: { optional?: boolean } = {},
): number | undefined {
  const value = record[field];
  if (optional && value === undefined) return undefined;
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    throw new ProfileDataError(
      `Local profile ${field} must be a non-negative safe integer`,
    );
  }
  return value;
}

function optionalBoolean(
  record: UnknownRecord,
  field: string,
  fallback: boolean,
): boolean {
  const value = record[field];
  if (value === undefined) return fallback;
  if (typeof value !== "boolean") {
    throw new ProfileDataError(`Local profile ${field} must be a boolean`);
  }
  return value;
}

function validateExternalImage(record: UnknownRecord, field: string): boolean {
  const value = safeString(record, field, { nullable: true, optional: true });
  if (!value) return false;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new ProfileDataError(
      `Local profile ${field} must be an absolute URL`,
    );
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new ProfileDataError(
      `Local profile ${field} uses an unsupported URL scheme`,
    );
  }
  return true;
}

function validateGroupBadges(record: UnknownRecord): void {
  const value = record.group_badges;
  if (value === undefined) return;
  if (!Array.isArray(value)) {
    throw new ProfileDataError("Local profile group_badges must be an array");
  }
  value.forEach((badge, index) => {
    if (!isRecord(badge)) {
      throw new ProfileDataError(
        `Local profile group badge ${index} must be an object`,
      );
    }
    safeString(badge, "group_id");
    safeString(badge, "username");
    validateExternalImage(badge, "profile_image_url");
    safeString(badge, "role");
  });
}

type ValidatedProfileRow = Omit<LocalProfile, "posts" | "dataSource">;

function validateUsers(input: unknown): ValidatedProfileRow[] {
  if (!Array.isArray(input)) {
    throw new ProfileDataError("Local profile users must be an array");
  }
  const identities = new Set<string>();
  return input.map((value, index) => {
    if (!isRecord(value)) {
      throw new ProfileDataError(
        `Local profile user ${index} must be an object`,
      );
    }
    const address = safeString(value, "address", {
      allowEmpty: true,
    }) as string;
    const userId = safeString(value, "userId", { optional: true }) as
      | string
      | undefined;
    if (!address && (!userId || !isValidProfileIdentifier(userId))) {
      throw new ProfileDataError(
        `Local profile user ${index} requires a usable user id when its wallet is absent`,
      );
    }
    for (const identity of new Set([
      ...(address ? [address] : []),
      ...(userId ? [userId] : []),
    ])) {
      if (identities.has(identity)) {
        throw new ProfileDataError(
          `Local profile user ${index} repeats an identity`,
        );
      }
      identities.add(identity);
    }

    const username = safeString(value, "username", { nullable: true }) as
      | string
      | null;
    const bio = safeString(value, "bio", {
      nullable: true,
      allowEmpty: true,
    }) as string | null;
    const xUsername = safeString(value, "x_username", { nullable: true }) as
      | string
      | null;
    const kind = value.kind ?? "person";
    if (kind !== "person" && kind !== "group") {
      throw new ProfileDataError(
        `Local profile user ${index} has an unsupported account kind`,
      );
    }
    const followers = nonnegativeInteger(value, "followers") as number;
    const following = nonnegativeInteger(value, "following") as number;
    const memberCount =
      nonnegativeInteger(value, "member_count", {
        optional: true,
      }) ?? 0;
    validateGroupBadges(value);
    const hasRecordedAvatar = validateExternalImage(value, "profile_image");
    validateExternalImage(value, "header_image_url");

    const canonicalSvmWallet = safeString(value, "canonical_svm_wallet", {
      optional: true,
      allowEmpty: true,
    });
    const canonicalEvmWallet = safeString(value, "canonical_evm_wallet", {
      optional: true,
      allowEmpty: true,
    });
    const canonicalWallet = canonicalSvmWallet || canonicalEvmWallet;
    if (canonicalWallet && canonicalWallet !== address) {
      throw new ProfileDataError(
        `Local profile user ${index} has an inconsistent canonical wallet`,
      );
    }

    const displayName =
      username?.trim() ||
      (address
        ? `${address.slice(0, 6)}…${address.slice(-4)}`
        : "Unnamed local account");
    return {
      address,
      userId,
      displayName,
      username,
      bio,
      kind,
      memberCount,
      followers,
      following,
      banned: optionalBoolean(value, "is_banned", false),
      isPumpUser: optionalBoolean(value, "is_pump_user", false),
      xUsername,
      hasRecordedAvatar,
    };
  });
}

function validatePostReferences(
  postsInput: unknown,
  users: ValidatedProfileRow[],
): void {
  if (!Array.isArray(postsInput)) {
    throw new ProfileDataError("Local profile posts must be an array");
  }
  const identities = new Set(
    users.flatMap((user) => [
      ...(user.address ? [user.address] : []),
      ...(user.userId ? [user.userId] : []),
    ]),
  );
  postsInput.forEach((value, index) => {
    if (!isRecord(value)) {
      throw new ProfileDataError(
        `Local profile post ${index} must be an object`,
      );
    }
    const authorId = safeString(value, "authorId") as string;
    if (!identities.has(authorId)) {
      throw new ProfileDataError(
        `Local profile post ${index} references an unknown author`,
      );
    }
    const createdAt = safeString(value, "createdAt", { nullable: true }) as
      | string
      | null;
    if (createdAt !== null && !Number.isFinite(Date.parse(createdAt))) {
      throw new ProfileDataError(
        `Local profile post ${index} has an invalid timestamp`,
      );
    }
  });
}

export function validateLocalProfiles(
  postsInput: unknown,
  usersInput: unknown,
): LocalProfileDataset {
  const users = validateUsers(usersInput);
  validatePostReferences(postsInput, users);
  const feed = validateLocalFeed(postsInput, usersInput);
  return {
    dataSource: LOCAL_PROFILE_DATA_SOURCE,
    profiles: users.map((user) => ({
      ...user,
      // An absent wallet is not an identity shared by every walletless account.
      // Feed adaptation resolves both id/address aliases to this stable user id.
      posts: feed.posts.filter((post) =>
        user.userId
          ? post.author.userId === user.userId
          : !!user.address && post.author.address === user.address,
      ),
      dataSource: LOCAL_PROFILE_DATA_SOURCE,
    })),
  };
}

export function resolveLocalProfile(
  dataset: LocalProfileDataset,
  identifier: string,
): LocalProfile | undefined {
  if (!isValidProfileIdentifier(identifier)) return undefined;
  return dataset.profiles.find(
    (profile) =>
      profile.address === identifier || profile.userId === identifier,
  );
}
