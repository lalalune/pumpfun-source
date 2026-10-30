import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { validateAgainstSchema } from "../packages/backend/src/schema-validator.ts";
import { test } from "node:test";
import {
  MAX_UPSTREAM_BYTES,
  normalizeUpstreamResponse,
  readBoundedJson,
  UpstreamValidationError,
} from "../packages/frontend/src/app/api/leaderboard/upstream.ts";

const position = {
  mint: "synthetic-mint",
  chainId: 1,
  symbol: "TEST",
  name: "Synthetic test position",
  imageUri: null,
};

const trader = {
  rank: 1,
  pnlSol: 1,
  pnlUsd: 25,
  pnlPercent: 5,
  buySpendSol: 2,
  lastRefreshedAtMs: 1_700_000_000_000,
  realizedPnlSol: 0.5,
  realizedPnlUsd: 10,
  unrealizedPnlSol: 0.5,
  unrealizedPnlUsd: 15,
  positionsCount: 1,
  topPositions: [position],
  walletAddress: "synthetic-wallet",
  username: "synthetic-test-user",
  profileImage: null,
  xUsername: null,
  isVerified: false,
  verifiedBadgeVisible: true,
  userId: "synthetic-user-id",
};

const creator = {
  rank: 1,
  userId: "synthetic-user-id",
  username: "synthetic-test-creator",
  profileImageUrl: null,
  isVerified: false,
  verifiedBadgeVisible: true,
  twitterId: null,
  twitterUrl: null,
  wallets: ["synthetic-wallet"],
  totalPaidUsdc: 20,
  payoutCount: 2,
  lastPaidAt: "2026-10-28T00:00:00.000Z",
  walletAddress: "synthetic-wallet",
};

const competitionEntry = {
  entryId: "synthetic-entry",
  participantId: "synthetic-participant",
  kind: "person",
  rank: 1,
  pnlUsd: 30,
  realizedPnlUsd: 20,
  unrealizedPnlUsd: 10,
  buySpendSol: 2,
  memberCount: 1,
  membersFresh: 1,
  struck: false,
  lastRefreshedAtMs: 1_700_000_000_000,
  positionsCount: 1,
  topPositions: [position],
  walletAddress: "synthetic-wallet",
  username: "synthetic-test-entrant",
  profileImageUrl: null,
  isVerified: false,
  verifiedBadgeVisible: true,
};

const competition = {
  id: "synthetic-competition-id",
  slug: "synthetic-competition",
  kind: "person",
  title: "Synthetic contract test competition",
  description: "Test-only contract fixture.",
  prizeCopy: "$0 test fixture",
  imageUrl: null,
  prizes: [{ rankFrom: 1, rankTo: 1, amount: "$0" }],
  registrationOpensAt: "2026-10-20T00:00:00.000Z",
  registrationClosesAt: "2026-10-30T00:00:00.000Z",
  startsAt: "2026-10-21T00:00:00.000Z",
  endsAt: "2026-10-30T00:00:00.000Z",
  minMembers: 1,
  maxMembers: 1,
  maxEntries: 50,
  entriesCount: 1,
  participants: 1,
  joinable: true,
  phase: "live",
  isFinal: false,
  top: [competitionEntry],
  winners: [],
};

test("normalizes documented trader and creator responses", () => {
  const traders = normalizeUpstreamResponse(
    "traders",
    {
      entries: [trader],
      periodType: 0,
      periodLabel: "Daily",
      windowStartSec: 1_700_000_000,
    },
    { page: 1, competitionId: null },
  );
  assert.equal(traders.kind, "traders");
  assert.equal(traders.entries[0].walletAddress, "synthetic-wallet");
  assert.equal(Object.hasOwn(traders.entries[0], "profileImage"), false);

  const creators = normalizeUpstreamResponse(
    "creators",
    {
      entries: [creator],
      totalEarners: 41,
      generatedAt: "2026-10-28T00:00:00.000Z",
    },
    { page: 3, competitionId: null },
  );
  assert.equal(creators.kind, "creators");
  assert.equal(creators.page, 3);
  assert.equal(creators.entries[0].totalPaidUsdc, 20);
});

// These payloads are synthetic contract cases, not observed production rankings.
const developerSpec = JSON.parse(
  readFileSync(new URL("../contracts/developer.openapi.json", import.meta.url), "utf8"),
);
const traderResponseSchema =
  developerSpec.paths["/pnl-leaderboard"].get.responses["200"].content[
    "application/json"
  ].schema;
const declaredPeriodTypes =
  traderResponseSchema.properties.periodType.anyOf.flatMap((branch) => branch.enum);

test("accepts every documented numeric PNL period type without changing the board", () => {
  assert.deepEqual(declaredPeriodTypes, [0, 1, 2, 3]);
  const entries = [
    { ...trader, rank: 7, pnlUsd: -25.125, username: null, userId: null },
    { ...trader, rank: 3, pnlUsd: 10.625, walletAddress: "synthetic-other-wallet" },
  ];
  for (const periodType of declaredPeriodTypes) {
    const payload = {
      entries,
      periodType,
      periodLabel: "Synthetic period label",
      windowStartSec: 1_700_000_000,
    };
    const before = structuredClone(payload);
    assert.deepEqual(
      validateAgainstSchema(payload, traderResponseSchema, "$", developerSpec),
      [],
    );
    const result = normalizeUpstreamResponse("traders", payload, {
      page: 1,
      competitionId: null,
    });
    assert.equal(result.kind, "traders");
    assert.deepEqual(
      result.entries.map((row) => [row.rank, row.pnlUsd, row.walletAddress]),
      entries.map((row) => [row.rank, row.pnlUsd, row.walletAddress]),
    );
    assert.equal(result.entries[0].username, null);
    assert.equal(result.entries[0].userId, null);
    assert.equal(result.periodLabel, payload.periodLabel);
    assert.equal(result.windowStartSec, payload.windowStartSec);
    assert.deepEqual(payload, before);
  }
});

test("rejects request period strings and other undeclared response period types", () => {
  for (const periodType of [
    "daily", "weekly", "monthly", "0", -1, 4, 0.5,
    null, undefined, true, {}, [], NaN, Infinity,
  ]) {
    const payload = {
      entries: [trader],
      periodType,
      periodLabel: "Synthetic period label",
      windowStartSec: 1_700_000_000,
    };
    assert.notDeepEqual(
      validateAgainstSchema(payload, traderResponseSchema, "$", developerSpec),
      [],
    );
    assert.throws(
      () => normalizeUpstreamResponse("traders", payload, {
        page: 1,
        competitionId: null,
      }),
      (error) => error instanceof UpstreamValidationError && /periodType/.test(error.message),
    );
  }
});

test("normalizes competition lists and ranked entry detail", () => {
  const list = normalizeUpstreamResponse(
    "competitions",
    { upcoming: [], live: [competition], past: [] },
    { page: 1, competitionId: null },
  );
  assert.equal(list.kind, "competitions");
  assert.equal(list.live[0].slug, "synthetic-competition");

  const detail = normalizeUpstreamResponse(
    "competitions",
    {
      competition,
      leaderboard: {
        builtAtMs: 1_700_000_000_000,
        startSec: 1_700_000_000,
        endSec: 1_700_003_600,
        totalRanked: 1,
        isFinal: false,
        entries: [competitionEntry],
      },
    },
    { page: 1, competitionId: "synthetic-competition" },
  );
  assert.equal(detail.kind, "competition-detail");
  assert.equal(detail.entries[0].entryId, "synthetic-entry");
});

test("rejects missing fields, unsupported competition enums and oversized arrays", () => {
  assert.throws(
    () =>
      normalizeUpstreamResponse(
        "traders",
        {
          entries: [{ ...trader, pnlUsd: "25" }],
          periodType: 0,
          periodLabel: "Synthetic period label",
          windowStartSec: 1_700_000_000,
        },
        { page: 1, competitionId: null },
      ),
    UpstreamValidationError,
  );
  assert.throws(
    () =>
      normalizeUpstreamResponse(
        "competitions",
        {
          upcoming: [],
          live: [{ ...competition, kind: "unknown-future-kind" }],
          past: [],
        },
        { page: 1, competitionId: null },
      ),
    /unsupported/,
  );
  assert.throws(
    () =>
      normalizeUpstreamResponse(
        "traders",
        {
          entries: Array.from({ length: 101 }, () => trader),
          periodType: 0,
          periodLabel: "Daily",
          windowStartSec: 1_700_000_000,
        },
        { page: 1, competitionId: null },
      ),
    /at most 100/,
  );
});

test("bounded JSON reader accepts JSON and rejects an oversized body", async () => {
  const parsed = await readBoundedJson(
    new Response(JSON.stringify({ ok: true }), {
      headers: { "Content-Type": "application/json" },
    }),
  );
  assert.deepEqual(parsed, { ok: true });

  await assert.rejects(
    readBoundedJson(new Response(new Uint8Array(MAX_UPSTREAM_BYTES + 1))),
    /too large/,
  );
});
