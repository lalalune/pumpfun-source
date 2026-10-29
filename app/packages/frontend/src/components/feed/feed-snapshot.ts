import "server-only";

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  FeedDataError,
  POSTS_SEED_SHA256,
  USERS_SEED_SHA256,
  validateLocalFeed,
  type LocalFeedDataset,
} from "./feed-data";

export type LocalFeedLoadResult =
  | { ok: true; dataset: LocalFeedDataset }
  | { ok: false; error: string };

function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function parseBoundSeed(
  label: "posts" | "users",
  bytes: Uint8Array,
  expectedSha256: string,
): unknown {
  const actualSha256 = sha256(bytes);
  if (actualSha256 !== expectedSha256) {
    throw new FeedDataError(
      `Local ${label} seed SHA-256 mismatch: expected ${expectedSha256}, received ${actualSha256}`,
    );
  }
  try {
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch (error) {
    throw new FeedDataError(
      `Local ${label} seed is not valid UTF-8 JSON: ${error instanceof Error ? error.message : "unknown parse failure"}`,
    );
  }
}

export async function loadLocalFeed(): Promise<LocalFeedLoadResult> {
  try {
    const backendSource = resolve(process.cwd(), "../backend/src");
    const [postsBytes, usersBytes] = await Promise.all([
      readFile(resolve(backendSource, "posts-seed.json")),
      readFile(resolve(backendSource, "users-seed.json")),
    ]);
    return {
      ok: true,
      dataset: validateLocalFeed(
        parseBoundSeed("posts", postsBytes, POSTS_SEED_SHA256),
        parseBoundSeed("users", usersBytes, USERS_SEED_SHA256),
        { includeQuotes: true },
      ),
    };
  } catch (error) {
    return {
      ok: false,
      error:
        error instanceof Error
          ? error.message
          : "Unknown local feed validation failure",
    };
  }
}
