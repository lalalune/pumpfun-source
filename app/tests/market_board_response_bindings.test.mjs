import assert from "node:assert/strict";
import test from "node:test";
import {
  mkdtemp,
  mkdir,
  copyFile,
  readFile,
  writeFile,
  rm,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { verifyMarketBoardResponse } from "../scripts/verify-market-board-response.mjs";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
test("real variants, existing request attribution and actual response handoff authenticate", async () => {
  await verifyMarketBoardResponse(ROOT);
  const c = JSON.parse(
    await readFile(
      new URL(
        "../reconstruction/market-board-response/contract.json",
        import.meta.url,
      ),
    ),
  );
  assert.equal(c.variants.length, 2);
  assert.equal(c.explicitPorts.retainChainId.exposureVariants.length, 3);
  assert.equal(c.handoff.boardResponse.expression, "(0,R.$)(n)");
  assert.equal(c.handoff.localPage.expression, "u.slice(c,c+f)");
  assert.equal(
    c.handoff.wrapperExport.expression,
    "function(e,t){return(0,c.q)(e,t)}",
  );
  assert.equal(c.handoff.initialSeedGate.expression, "H&&Q&&(0,I.$)(H)");
  assert.equal(
    c.handoff.initialSeedMode.expression,
    '"social-terminal"===(0,u.y)()',
  );
});
test("changed captured variant and maintained adapter cannot reuse retained source bindings", async (t) => {
  const root = await mkdtemp(path.join(tmpdir(), "board-response-binding-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const fixed = [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    "contracts/market-board-bindings.json",
    "reconstruction/market-board-response/contract.json",
    "reconstruction/market-board-response/response.mjs",
  ];
  const source = JSON.parse(await readFile(path.join(ROOT, fixed[2]))).sources;
  const objects = [
    ...new Set([
      ...Object.keys(source),
      "evidence/web/objects/cf2bb278631744da.js",
      "evidence/web/objects/2c867fef5c76d400.js",
      "evidence/web/objects/fd402d4185b44ce9.js",
      "evidence/web/objects/27a1ee00eb5909ec.js",
    ]),
  ];
  for (const file of [...fixed, ...objects]) {
    await mkdir(path.dirname(path.join(root, file)), { recursive: true });
    await copyFile(path.join(ROOT, file), path.join(root, file));
  }
  await verifyMarketBoardResponse(root);
  const target = path.join(root, "evidence/web/objects/cf2bb278631744da.js");
  const bytes = await readFile(target);
  await writeFile(target, Buffer.concat([bytes, Buffer.from("\n")]));
  await assert.rejects(
    verifyMarketBoardResponse(root),
    /capture authentication failed/,
  );
  await writeFile(target, bytes);
  await writeFile(
    path.join(root, fixed.at(-1)),
    (await readFile(path.join(root, fixed.at(-1)), "utf8")) + "\n",
  );
  await assert.rejects(
    verifyMarketBoardResponse(root),
    /market response contract stale/,
  );
});
