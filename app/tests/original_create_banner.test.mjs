import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { recover, OUTPUT } from "../scripts/original-create-banner.mjs";
test("optional banner uses selected Create/common factories and preserves separate post-launch boundary", async () => {
  const result = await recover();
  assert.deepEqual(
    JSON.parse(
      await readFile(new URL(`../${OUTPUT}`, import.meta.url), "utf8"),
    ),
    result,
  );
  assert.equal(result.observed.maximumFiles, 1);
  assert.equal(result.localAdaptation.tokenMetadataChanged, false);
  assert.equal(result.localAdaptation.normalizationImplemented, false);
});
