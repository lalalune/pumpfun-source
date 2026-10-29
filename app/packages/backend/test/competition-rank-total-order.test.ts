import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const seed = () =>
  JSON.parse(
    readFileSync(
      new URL("../src/competitions-seed.json", import.meta.url),
      "utf8",
    ),
  );
import { CompetitionStore } from "../src/competitions-store.js";
test("equal-profit entry ranks do not depend on seed insertion order", () => {
  const data = seed();
  const c = data.find((c: any) => c.entries.length >= 2);
  c.entries = c.entries.slice(0, 2);
  Object.assign(c.entries[1], {
    pnlUsd: c.entries[0].pnlUsd,
    registeredAt: c.entries[0].registeredAt,
  });
  c.entries[0].entryId = "é";
  c.entries[1].entryId = "é";
  for (const e of c.entries) {
    e.struck = false;
    e.lastRefreshedAtMs = 1;
  }
  const ids = (d: any) =>
    new CompetitionStore(d)
      .getByIdOrSlug(c.id)!
      .leaderboard.entries.map((e) => e.entryId);
  const expected = ids(data);
  c.entries.reverse();
  assert.deepEqual(ids(data), expected);
});
