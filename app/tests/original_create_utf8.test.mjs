import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { recover, OUTPUT } from "../scripts/original-create-utf8.mjs";
test("Create limits bind nativeUTF8helper and both actual consumers with preserved codeunit input/description boundaries", async () => {
  const proof = await recover();
  assert.deepEqual(
    JSON.parse(
      await readFile(new URL(`../${OUTPUT}`, import.meta.url), "utf8"),
    ),
    proof,
  );
  assert.equal(proof.observed.actualValidatorConsumers, 2);
  assert.equal(proof.observed.nameUtf8Bytes, 32);
  assert.equal(proof.observed.tickerUtf8Bytes, 10);
  assert.equal(proof.observed.descriptionCodeUnits, 2000);
});
