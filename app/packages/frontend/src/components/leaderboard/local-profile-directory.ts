import "server-only";

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { POSTS_SEED_SHA256, USERS_SEED_SHA256 } from "../feed/feed-data";
import {
  parseProfileSeedBytes,
  validateLocalProfiles,
  isValidProfileIdentifier,
} from "../profile/profile-data";
import type { LocalRankingProfile } from "./local-profile-identity";

type SeedReader = (name: "posts" | "users") => Promise<Uint8Array>;
const readSeed: SeedReader = (name) =>
  readFile(resolve(process.cwd(), `../backend/src/${name}-seed.json`));

/** Uses the same byte pins/validator as the existing offline profile page. */
export async function loadLocalRankingProfiles(
  read: SeedReader = readSeed,
): Promise<LocalRankingProfile[]> {
  try {
    const [posts, users] = await Promise.all([read("posts"), read("users")]);
    const dataset = validateLocalProfiles(
      parseProfileSeedBytes("posts", posts, POSTS_SEED_SHA256),
      parseProfileSeedBytes("users", users, USERS_SEED_SHA256),
    );
    return dataset.profiles
      .filter(
        (profile) =>
          profile.kind === "person" &&
          isValidProfileIdentifier(profile.address),
      )
      .map((profile) => ({
        walletAddress: profile.address,
        userId: profile.userId ?? null,
        username: profile.username,
      }));
  } catch {
    // Standings may still be read, but uncertain identity links stay unavailable.
    return [];
  }
}
