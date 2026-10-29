import test from "node:test";
import assert from "node:assert/strict";
import {
  buildMayhemQuery,
  mayhemStateParameter,
} from "../packages/frontend/src/app/mayhem/mayhem-data.ts";
test("unknown direct filters cannot escape as remote state parameters", () => {
  for (const filter of ["completed", "unknown", null, 42]) {
    assert.throws(() => buildMayhemQuery({ filter }), /filter/);
    assert.throws(() => mayhemStateParameter(filter), /filter/);
  }
  assert.equal(
    buildMayhemQuery({ filter: "ended" }).get("mayhemState"),
    "completed",
  );
});
