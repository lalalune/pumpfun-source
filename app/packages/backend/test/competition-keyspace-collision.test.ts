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
test("one competition ID cannot shadow another competition slug", () => {
  const data = seed();
  data[0].id = data[1].slug.toUpperCase();
  assert.throws(() => new CompetitionStore(data), /keyspace/);
  const own = seed();
  own[0].id = own[0].slug;
  assert.doesNotThrow(() => new CompetitionStore(own));
});
