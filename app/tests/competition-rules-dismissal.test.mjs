import assert from "node:assert/strict";
import { test } from "node:test";
import {
  readFile,
  mkdtemp,
  mkdir,
  link,
  writeFile,
  rm,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  rulesDismissalEvidence,
  verifyRulesDismissal,
} from "../scripts/verify-competition-rules-dismissal.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
test("actual Rules caller/default/backdrop/intentional dismissal source chain binds native dialog", async () => {
  const evidence = await verifyRulesDismissal();
  assert.equal(
    evidence.wrapperAstSha256,
    "c38f55e1f033262de49e78d01b358e8f9a11dcdfb772c299c57a5dc89eb407f1",
  );
  assert.equal(evidence.source.selectedEntries.length, 5);
  assert.ok(evidence.witnesses.every((w) => w.sha256 && w.utf8 && w.utf16));
});
test("native gate rejects missing/disabled dismissal and a disconnected extra dialog", async (t) => {
  const evidence = await rulesDismissalEvidence(),
    dir = await mkdtemp(path.join(APP, ".rules-source-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const names = new Set([
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "reconstruction/competition-rules-dismissal/contract.json",
    ...evidence.source.selectedEntries.flatMap((r) =>
      r.origins.map((o) => o.source),
    ),
  ]);
  for (const name of names) {
    const dest = path.join(dir, name);
    await mkdir(path.dirname(dest), { recursive: true });
    await link(path.join(APP, name), dest);
  }
  const name = "packages/frontend/src/app/leaderboard/competition-rules.tsx",
    dest = path.join(dir, name);
  await mkdir(path.dirname(dest), { recursive: true });
  const actual = await readFile(path.join(APP, name), "utf8");
  await writeFile(dest, actual);
  await verifyRulesDismissal(dir);
  for (const changed of [
    actual.replace('closedby="any"', 'closedby="closerequest"'),
    actual.replace('closedby="any"', ""),
    actual + '\nfunction disconnected(){return <dialog closedby="any"/>;}\n',
  ]) {
    await writeFile(dest, changed);
    await assert.rejects(verifyRulesDismissal(dir));
  }
});
