import {
  parseProfileSeedBytes,
  resolveLocalProfile,
  type LocalProfile,
  type LocalProfileDataset,
} from "./profile-data";
import { isValidProfileIdentifier } from "./profile-identifier";

export const FOLLOWING_SEED_SHA256 =
  "37a0e7710055e94dd6035e3e6c418eac16797095471601ed059440ee97530dae";

export type LocalFollowMember = Pick<
  LocalProfile,
  "displayName" | "kind" | "banned"
> & {
  identifier: string;
};

export type LocalFollowGraph = {
  followers: LocalFollowMember[];
  following: LocalFollowMember[];
};

export type LocalFollowGraphResult =
  | { ok: true; graph: LocalFollowGraph }
  | { ok: false };

/** Small offline graph only; aggregate profile counters do not define edges. */
export function localFollowGraph(
  input: unknown,
  dataset: LocalProfileDataset,
  subject: LocalProfile,
): LocalFollowGraph {
  if (!Array.isArray(input))
    throw new Error("Local following seed must be an array.");
  const seen = new Set<string>();
  const edges = input.map((value: unknown) => {
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new Error("Invalid local follow edge.");
    const edge = value as Record<string, unknown>;
    if (
      typeof edge.follower_id !== "string" ||
      typeof edge.following_id !== "string" ||
      !Number.isSafeInteger(edge.timestamp) ||
      (edge.timestamp as number) < 0
    ) {
      throw new Error("Invalid local follow edge.");
    }
    const follower = resolveLocalProfile(dataset, edge.follower_id);
    const following = resolveLocalProfile(dataset, edge.following_id);
    if (!follower || !following)
      throw new Error("Unresolved local follow identity.");
    const key = JSON.stringify([identity(follower), identity(following)]);
    if (seen.has(key)) throw new Error("Duplicate local follow edge.");
    seen.add(key);
    return { follower, following };
  });
  function members(direction: "followers" | "following"): LocalFollowMember[] {
    return (
      edges
        .filter(
          (edge) =>
            identity(
              direction === "followers" ? edge.following : edge.follower,
            ) === identity(subject),
        )
        .map((edge) =>
          direction === "followers" ? edge.follower : edge.following,
        )
        // Match the local FollowingStore's default followers ordering and tie-breaks.
        .sort(
          (a, b) =>
            b.followers - a.followers ||
            compare(a.username ?? "\uffff", b.username ?? "\uffff") ||
            compare(identity(a), identity(b)),
        )
        .map((profile) => ({
          identifier: identity(profile),
          displayName: profile.displayName,
          kind: profile.kind,
          banned: profile.banned,
        }))
    );
  }
  return { followers: members("followers"), following: members("following") };
}

function identity(profile: LocalProfile): string {
  if (profile.userId && isValidProfileIdentifier(profile.userId))
    return profile.userId;
  if (isValidProfileIdentifier(profile.address)) return profile.address;
  throw new Error("Unroutable local follow identity.");
}

function compare(a: string, b: string): number {
  return a === b ? 0 : a < b ? -1 : 1;
}

/** The server supplies file reads; failures never turn into an empty graph. */
export async function loadLocalFollowGraph(
  dataset: LocalProfileDataset,
  subject: LocalProfile,
  readBytes: () => Promise<Uint8Array>,
): Promise<LocalFollowGraphResult> {
  try {
    const input = parseProfileSeedBytes(
      "following",
      await readBytes(),
      FOLLOWING_SEED_SHA256,
    );
    return { ok: true, graph: localFollowGraph(input, dataset, subject) };
  } catch {
    return { ok: false };
  }
}
