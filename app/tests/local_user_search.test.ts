import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { localUserSearchResponse } from "../packages/frontend/src/lib/local-user-search-server.ts";
import { isLocalUserSearchRows } from "../packages/frontend/src/lib/local-user-search-data.ts";
import {
  createUserSearchQuery,
  selectUserSearchPages,
} from "../reconstruction/user-search/query.mjs";

const readSeed = (name: "posts" | "users") =>
  readFile(
    new URL(`../packages/backend/src/${name}-seed.json`, import.meta.url),
  );
const request = (query: string) =>
  new Request(`http://localhost/api/local-users/search?${query}`);

test("local GET searches the validated model and preserves empty wallet labels", async () => {
  const response = await localUserSearchResponse(request("q=ALICE"), readSeed);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(
    response.headers.get("x-reconstruction-data-source"),
    "synthetic-seed-play",
  );
  const rows = await response.json();
  assert.equal(isLocalUserSearchRows(rows), true);
  assert.equal(rows.length, 1);
  assert.equal(rows[0].identifier, "user-001");
  assert.equal(rows[0].wallet_label, "");
  assert.ok(Object.hasOwn(rows[0], "wallet_label"));
  assert.doesNotMatch(
    JSON.stringify(rows),
    /https?:|profile_image|bio|header_image|x_username|canonical_svm_wallet/,
  );
  assert.deepEqual(selectUserSearchPages({ pages: [rows] }), rows);
});

test("all five exact seeded identities remain searchable with unmodified served order", async () => {
  const response = await localUserSearchResponse(
    request("q=user-00"),
    readSeed,
  );
  const rows = await response.json();
  assert.deepEqual(
    rows.map((row: { identifier: string }) => row.identifier),
    ["user-001", "user-002", "user-003", "user-004", "user-005"],
  );
  assert.equal(rows[2].wallet_label, "external-wallet");
  assert.equal(rows[4].banned, true);
  assert.deepEqual(selectUserSearchPages({ pages: [rows] }), rows);
  const empty = await localUserSearchResponse(
    request("q=missing-name"),
    readSeed,
  );
  assert.equal(empty.status, 200);
  assert.deepEqual(await empty.json(), []);
});

test("local query boundaries fail before reading files", async () => {
  let reads = 0;
  for (const query of [
    "",
    "q=a",
    "q=%20%20",
    "q=alice&q=bob",
    "q=alice&origin=https://example.com",
    `q=${"x".repeat(201)}`,
  ]) {
    assert.equal(
      (
        await localUserSearchResponse(request(query), async () => {
          reads++;
          return Buffer.from("[]");
        })
      ).status,
      400,
    );
  }
  assert.equal(reads, 0);
  assert.equal(
    (await localUserSearchResponse(request("q=%F0%9F%98%80"), readSeed)).status,
    200,
  );
});

test("missing or changed users and posts fail without exposing paths or fallback records", async () => {
  for (const name of ["users", "posts"] as const) {
    const missing = await localUserSearchResponse(
      request("q=alice"),
      async (selected) => {
        if (selected === name) throw new Error("private filesystem path");
        return readSeed(selected);
      },
    );
    assert.equal(missing.status, 503);
    assert.deepEqual(await missing.json(), {
      error: "LOCAL_USERS_UNAVAILABLE",
    });
    const changed = await localUserSearchResponse(
      request("q=alice"),
      async (selected) =>
        selected === name ? Buffer.from("[]") : readSeed(selected),
    );
    assert.equal(changed.status, 503);
    assert.deepEqual(await changed.json(), {
      error: "LOCAL_USERS_UNAVAILABLE",
    });
  }
});

test("host response admission rejects malformed display fields and mismatched navigation identities", () => {
  const row = {
    address: "wallet",
    userId: "id",
    identifier: "id",
    displayName: "Name",
    kind: "person",
    banned: false,
  };
  assert.equal(isLocalUserSearchRows([row]), true);
  assert.equal(isLocalUserSearchRows([row, row]), false);
  for (const bad of [
    { ...row, identifier: "other" },
    { ...row, displayName: {} },
    { ...row, wallet_label: null },
    { ...row, banned: "false" },
  ])
    assert.equal(isLocalUserSearchRows([bad]), false);
});

test("unchanged source query retains snapshots and identity selection for explicit local pages", async () => {
  const calls: unknown[] = [];
  const old = createUserSearchQuery(
    { searchTerm: "alice", debouncedTerm: "alice" },
    () => async (_operation, options) => {
      calls.push(options.query.searchTerm);
      return [];
    },
  );
  createUserSearchQuery(
    { searchTerm: "bob", debouncedTerm: "bob" },
    () => async () => [],
  );
  await old.queryOptions.queryFn({
    pageParam: 0,
    signal: new AbortController().signal,
  });
  assert.deepEqual(calls, ["alice"]);
  assert.equal(old.debounceMs, 500);
  assert.equal(
    createUserSearchQuery(
      { searchTerm: "a", debouncedTerm: "a" },
      () => async () => [],
    ).queryOptions.enabled,
    false,
  );
  const rows = [
    { userId: " id ", address: "wallet" },
    { userId: "id", address: "duplicate" },
    { address: "wallet", wallet_label: "" },
    { address: "labelled", wallet_label: "" },
  ];
  assert.deepEqual(selectUserSearchPages({ pages: [rows] }), [
    rows[0],
    rows[3],
  ]);
});
