import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { UserStore, type User } from "../../../backend/src/users-store";
import {
  POSTS_SEED_SHA256,
  USERS_SEED_SHA256,
} from "../components/feed/feed-data";
import {
  parseProfileSeedBytes,
  resolveLocalProfile,
  validateLocalProfiles,
} from "../components/profile/profile-data";
import type { LocalUserSearchRow } from "./local-user-search-data";

type SeedReader = (name: "posts" | "users") => Promise<Uint8Array>;
const readSeed: SeedReader = (name) =>
  readFile(resolve(process.cwd(), `../backend/src/${name}-seed.json`));
const headers = {
  "Cache-Control": "no-store",
  "X-Reconstruction-Data-Source": "synthetic-seed-play",
};

/** Local public read only. No upstream origin, API key or viewer/session is used. */
export async function localUserSearchResponse(
  request: Request,
  read: SeedReader = readSeed,
): Promise<Response> {
  const url = new URL(request.url);
  const term = url.searchParams.get("q")?.trim() ?? "";
  if (
    [...url.searchParams.keys()].some((key) => key !== "q") ||
    url.searchParams.getAll("q").length !== 1 ||
    term.length < 2 ||
    term.length > 200
  ) {
    return Response.json(
      { error: "LOCAL_QUERY_INVALID" },
      { status: 400, headers },
    );
  }
  try {
    const [posts, users] = await Promise.all([read("posts"), read("users")]);
    const rawUsers = parseProfileSeedBytes("users", users, USERS_SEED_SHA256);
    const dataset = validateLocalProfiles(
      parseProfileSeedBytes("posts", posts, POSTS_SEED_SHA256),
      rawUsers,
    );
    // The byte pin and profile validator establish this exact synthetic input.
    const storedUsers = rawUsers as User[];
    if (
      storedUsers.some(
        (row) =>
          row.wallet_label !== undefined &&
          typeof row.wallet_label !== "string",
      )
    )
      throw new Error("Invalid local wallet label.");
    const rows = new UserStore(storedUsers).search({
      searchTerm: term,
      includeLabelledWallets: true,
      offset: 0,
      limit: 20,
    });
    const result: LocalUserSearchRow[] = rows.map((row) => {
      const profile = resolveLocalProfile(dataset, row.userId || row.address);
      if (!profile) throw new Error("Unresolved local search identity.");
      return {
        address: profile.address,
        ...(profile.userId === undefined ? {} : { userId: profile.userId }),
        // Preserve absence versus the empty string for the original selector.
        ...(row.wallet_label === undefined
          ? {}
          : { wallet_label: row.wallet_label }),
        displayName: profile.displayName,
        identifier: profile.userId ?? profile.address,
        kind: profile.kind,
        banned: profile.banned,
      };
    });
    return Response.json(result, { headers });
  } catch {
    return Response.json(
      { error: "LOCAL_USERS_UNAVAILABLE" },
      { status: 503, headers },
    );
  }
}
