import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  POSTS_SEED_SHA256,
  USERS_SEED_SHA256,
} from "../packages/frontend/src/components/feed/feed-data.ts";
import {
  parseProfileSeedBytes,
  resolveLocalProfile,
  sha256,
  validateLocalProfiles,
} from "../packages/frontend/src/components/profile/profile-data.ts";
import {
  FOLLOWING_SEED_SHA256,
  loadLocalFollowGraph,
  localFollowGraph,
} from "../packages/frontend/src/components/profile/profile-follow-graph.ts";

test("graph links fall back to a routable wallet when an optional user id is unsafe", async () => {
  const users = JSON.parse(
    await readFile(
      new URL("../packages/backend/src/users-seed.json", import.meta.url),
      "utf8",
    ),
  );
  for (const unsafe of [
    ".",
    "..",
    "\ud800",
    "\udc00",
    "bad/id",
    " bad",
    "x".repeat(129),
  ]) {
    const input = structuredClone(users);
    input[1].userId = unsafe;
    const dataset = validateLocalProfiles([], input);
    const [alice, bob] = dataset.profiles;
    const before = structuredClone(dataset);
    const edge = {
      follower_id: bob.address,
      following_id: alice.userId,
      timestamp: 0,
    };
    const followers = localFollowGraph([edge], dataset, alice).followers;
    assert.equal(followers[0].identifier, bob.address);
    assert.equal(resolveLocalProfile(dataset, followers[0].identifier), bob);
    assert.equal(
      localFollowGraph([edge], dataset, bob).following[0].identifier,
      alice.userId,
    );
    assert.throws(
      () =>
        localFollowGraph(
          [edge, { ...edge, following_id: alice.address }],
          dataset,
          alice,
        ),
      /Duplicate local follow edge/,
    );
    assert.deepEqual(dataset, before);
  }
});

test("graph identity keeps valid Unicode and literal encoded user ids before wallet aliases", async () => {
  const users = JSON.parse(
    await readFile(
      new URL("../packages/backend/src/users-seed.json", import.meta.url),
      "utf8",
    ),
  );
  for (const identifier of [
    "é",
    "e\u0301",
    "😀",
    "%2e",
    "%2E%2E",
    "%2F",
    "%",
    "group:one",
  ]) {
    const input = structuredClone(users);
    input[1].userId = identifier;
    const dataset = validateLocalProfiles([], input);
    const [alice, bob] = dataset.profiles;
    const edge = {
      follower_id: bob.address,
      following_id: alice.address,
      timestamp: 0,
    };
    const graph = localFollowGraph([edge], dataset, alice);
    assert.equal(graph.followers[0].identifier, identifier);
    const pathname = new URL(
      `/profile/${encodeURIComponent(identifier)}`,
      "https://local.invalid",
    ).pathname;
    assert.equal(
      resolveLocalProfile(
        dataset,
        decodeURIComponent(pathname.slice("/profile/".length)),
      ),
      bob,
    );
    assert.throws(
      () =>
        localFollowGraph(
          [edge, { ...edge, follower_id: identifier }],
          dataset,
          alice,
        ),
      /Duplicate local follow edge/,
    );
  }
});

async function seeds() {
  const path = new URL("../packages/backend/src/", import.meta.url);
  const [posts, users, graphBytes] = await Promise.all(
    ["posts", "users", "following"].map((name) =>
      readFile(new URL(`${name}-seed.json`, path)),
    ),
  );
  const dataset = validateLocalProfiles(
    parseProfileSeedBytes("posts", posts, POSTS_SEED_SHA256),
    parseProfileSeedBytes("users", users, USERS_SEED_SHA256),
  );
  return {
    dataset,
    graphBytes,
    edges: JSON.parse(graphBytes.toString("utf8")),
  };
}

test("exact graph bytes resolve complete local directions without substituting aggregate counts", async () => {
  const { dataset, graphBytes, edges } = await seeds();
  const alice = resolveLocalProfile(dataset, "user-001")!;
  assert.equal(sha256(graphBytes), FOLLOWING_SEED_SHA256);
  const result = await loadLocalFollowGraph(
    dataset,
    alice,
    async () => graphBytes,
  );
  assert.equal(result.ok, true);
  if (!result.ok) return;
  assert.deepEqual(
    result.graph.followers.map((x) => x.identifier),
    ["user-004", "user-002", "user-005", "user-003"],
  );
  assert.deepEqual(
    result.graph.following.map((x) => x.identifier),
    ["user-004", "user-002"],
  );
  assert.equal(alice.followers, 1200);
  assert.equal(alice.following, 340);
  assert.deepEqual(
    localFollowGraph(
      edges,
      dataset,
      resolveLocalProfile(dataset, alice.address)!,
    ),
    result.graph,
  );
  assert.doesNotMatch(
    JSON.stringify(result),
    /https?:|QmAlice|QmBob|QmChad|profile_image|bio/,
  );
});

test("empty sides and groups/banned rows remain explicit rather than inferred", async () => {
  const { dataset, edges } = await seeds();
  const graph = localFollowGraph(
    edges,
    dataset,
    resolveLocalProfile(dataset, "user-003")!,
  );
  assert.deepEqual(graph.followers, []);
  assert.equal(graph.following.length, 3);
  const alice = localFollowGraph(
    edges,
    dataset,
    resolveLocalProfile(dataset, "user-001")!,
  );
  assert.equal(alice.followers[0].kind, "group");
  assert.equal(
    alice.followers.find((row) => row.identifier === "user-005")!.banned,
    true,
  );
  assert.deepEqual(localFollowGraph([], dataset, dataset.profiles[0]), {
    followers: [],
    following: [],
  });
});

test("default follower ordering is stable across edge input order and equal counts", async () => {
  const { dataset, edges } = await seeds();
  for (const profile of dataset.profiles) profile.followers = 1;
  const alice = resolveLocalProfile(dataset, "user-001")!;
  const first = localFollowGraph(edges, dataset, alice);
  assert.deepEqual(
    first.followers.map((x) => x.identifier),
    ["user-005", "user-002", "user-004", "user-003"],
  );
  assert.deepEqual(
    localFollowGraph([...edges].reverse(), dataset, alice),
    first,
  );
  dataset.profiles.forEach((profile) => {
    profile.username = null;
  });
  assert.deepEqual(
    localFollowGraph(edges, dataset, alice).followers.map((x) => x.identifier),
    ["user-002", "user-003", "user-004", "user-005"],
  );
});

test("walletless identities use their stable id and wallet-only identities remain reachable", async () => {
  const { dataset } = await seeds();
  const [alice, bob] = dataset.profiles;
  alice.address = "";
  delete bob.userId;
  const graph = localFollowGraph(
    [{ follower_id: bob.address, following_id: alice.userId, timestamp: 0 }],
    dataset,
    alice,
  );
  assert.equal(graph.followers[0].identifier, bob.address);
  assert.deepEqual(
    localFollowGraph(
      [{ follower_id: alice.userId, following_id: bob.address, timestamp: 0 }],
      dataset,
      alice,
    ).following.map((x) => x.identifier),
    [bob.address],
  );
});

test("unknown identities, alias duplicates and malformed edges fail the whole graph", async () => {
  const { dataset, edges } = await seeds();
  const alice = dataset.profiles[0];
  for (const invalid of [
    null,
    {},
    [null],
    [{ ...edges[0], follower_id: "missing" }],
    [{ ...edges[0], timestamp: -1 }],
    [{ ...edges[0], timestamp: 1.5 }],
    [{ ...edges[0], timestamp: "0" }],
    [edges[0], edges[0]],
    [edges[0], { ...edges[0], following_id: alice.address }],
  ]) {
    assert.throws(() => localFollowGraph(invalid, dataset, alice));
  }
});

test("missing, changed or unresolved graph data does not become a fabricated empty graph", async () => {
  const { dataset, graphBytes } = await seeds();
  const alice = dataset.profiles[0];
  const before = structuredClone(dataset);
  assert.deepEqual(
    await loadLocalFollowGraph(dataset, alice, async () => {
      throw new Error("ENOENT");
    }),
    { ok: false },
  );
  assert.deepEqual(
    await loadLocalFollowGraph(dataset, alice, async () => Buffer.from("[]")),
    { ok: false },
  );
  assert.deepEqual(
    await loadLocalFollowGraph(dataset, alice, async () =>
      Buffer.concat([graphBytes, Buffer.from(" ")]),
    ),
    { ok: false },
  );
  assert.deepEqual(dataset, before);
  const missing = { ...dataset, profiles: dataset.profiles.slice(0, 4) };
  assert.deepEqual(
    await loadLocalFollowGraph(missing, alice, async () => graphBytes),
    { ok: false },
  );
});
