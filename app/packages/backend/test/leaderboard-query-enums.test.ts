import test from "node:test";
import assert from "node:assert/strict";
import { LeaderboardStore } from "../src/leaderboard-store.js";
test("unsupported board enums cannot generate undefined metadata", () => {
  const s = new LeaderboardStore();
  assert.throws(() => s.getBoard({ period: "all" } as any), /query/);
  assert.throws(
    () => s.getBoard({ period: "daily", sort: "other" } as any),
    /query/,
  );
  assert.equal(s.getBoard({ period: "daily" }).periodType, 1);
});
