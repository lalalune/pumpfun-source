import assert from "node:assert/strict";
import test from "node:test";
import { createRequire } from "node:module";
import Fastify from "fastify";
import seed from "../src/home-feed-seed.json" with { type: "json" };
import { registerHomeFeedRoutes } from "../src/home-feed-routes.js";
import {
  HomeFeedSeedError,
  HomeFeedStore,
  validateHomeFeedSeed,
} from "../src/home-feed-store.js";
// The frontend package is CommonJS under tsx; load its maintained pure guard
// without importing server-only, browser code or a captured factory.
const { validateNativeFeedPage } = createRequire(import.meta.url)(
  "../../frontend/src/components/feed/native-feed-data.ts",
) as typeof import("../../frontend/src/components/feed/native-feed-data.js");

const fields = [
  "coinMint",
  "coinName",
  "symbol",
  "authorId",
  "authorName",
  "thesis",
] as const;

function oneRecord() {
  // These are explicit local examples, not captured market records.
  const input = JSON.parse(JSON.stringify(seed)) as typeof seed;
  input.records = [input.records.find((row) => !row.hidden && !row.deleted)!];
  return input;
}

test("home-feed admission rejects whitespace-only required strings", () => {
  for (const field of fields) {
    for (const blank of [
      "",
      " ",
      "   ",
      "\u00a0",
      "\u2003",
      "\u3000",
      "\ufeff",
      " \u00a0\u2003 ",
    ]) {
      const input = oneRecord();
      input.records[0][field] = blank;
      assert.throws(
        () => validateHomeFeedSeed(input),
        HomeFeedSeedError,
        `${field}: ${JSON.stringify(blank)}`,
      );
      assert.throws(
        () => new HomeFeedStore(input),
        HomeFeedSeedError,
        `${field}: ${JSON.stringify(blank)}`,
      );
    }
  }
});

test("accepted required strings survive actual ranked/new routes and the maintained feed consumer unchanged", async () => {
  for (const value of [" ordinary ", "\u00a0Café\u3000", " 🚀東京 "]) {
    const input = oneRecord();
    for (const field of fields) input.records[0][field] = value;
    const store = new HomeFeedStore(input);
    const app = Fastify();
    registerHomeFeedRoutes(app, store);
    try {
      for (const [route, kind] of [
        ["/services/frontend/home-feed?pageSize=3", "ranked"],
        ["/services/frontend/home-feed/new?pageSize=3", "newest"],
      ] as const) {
        const response = await app.inject(route);
        assert.equal(response.statusCode, 200);
        assert.equal(response.headers["cache-control"], "no-store");
        assert.equal(
          response.headers["x-reconstruction-data-source"],
          "synthetic-home-feed-local-v1",
        );
        const page = validateNativeFeedPage(response.json(), kind);
        assert.equal(page.coins.length, 1);
        for (const field of fields)
          assert.equal(page.coins[0][field], value, field);
      }
      for (const field of fields)
        assert.equal(store.snapshotRecords()[0][field], value, field);
    } finally {
      await app.close();
    }
  }
});

test("the unchanged hash-bound seed still serves both maintained feed views", async () => {
  const app = Fastify();
  registerHomeFeedRoutes(app, new HomeFeedStore());
  try {
    for (const [route, kind] of [
      ["/services/frontend/home-feed?pageSize=3", "ranked"],
      ["/services/frontend/home-feed/new?pageSize=3", "newest"],
    ] as const) {
      const response = await app.inject(route);
      assert.equal(response.statusCode, 200);
      assert.ok(validateNativeFeedPage(response.json(), kind).coins.length > 0);
    }
  } finally {
    await app.close();
  }
});
