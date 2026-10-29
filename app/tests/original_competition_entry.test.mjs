import assert from "node:assert/strict";
import { test } from "node:test";
import {
  mkdtemp,
  mkdir,
  readFile,
  writeFile,
  copyFile,
  rm,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import React from "../packages/frontend/node_modules/react/index.js";
import {
  jsx,
  jsxs,
} from "../packages/frontend/node_modules/react/jsx-runtime.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import { useMemoCache } from "../packages/frontend/src/components/leaderboard/original-prize-formats.mjs";
import {
  createEntryHelpers,
  squadVariants,
  imageVariants,
} from "../packages/frontend/src/components/leaderboard/entry/entry-helpers.mjs";
import { verifyCompetitionEntry } from "../scripts/original-competition-entry.mjs";
import { validateAgainstSchema } from "../packages/backend/src/schema-validator.ts";
import {
  rows,
  wallet,
  syntheticTranslate,
} from "./fixtures/competition-entry-data.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { transform } = createRequire(sdk.resolve("tsup"))("esbuild");
const contexts = squadVariants.flatMap((s) =>
  imageVariants.map((i) => ({
    squadVariant: s.sha256,
    imageVariant: i.sha256,
    Intl,
  })),
);
test("complete X, original SVGs, actual caller/DTO and every selected origin are source-authenticated", async () => {
  const c = await verifyCompetitionEntry();
  assert.equal(c.source.selectedIndexEntries.length, 17);
  for (const label of [
    "COMPLETE actual competition entry row X",
    "actual consumer: supplied entry and already selected prize",
    "COMPLETE original verified badge component",
    "COMPLETE used original crown icon",
    "COMPLETE used original SVG wrapper",
  ])
    assert.ok(
      c.witnesses.some((w) => w.label === label),
      label,
    );
  assert.ok(c.witnesses.every((w) => w.sha256 && w.utf16 && w.utf8));
});
test("source gate rejects full component behavior drift and independent contract edits", async (t) => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "entry-source-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const c = JSON.parse(
    await readFile(
      path.join(APP, "reconstruction/competition-entry/contract.json"),
    ),
  );
  const names = new Set([
    "scripts/original-contracts/source.mjs",
    "evidence/web/manifest.json",
    "recovered/modules.json",
    ...c.source.selectedIndexEntries.flatMap((r) =>
      r.origins.map((o) => o.source),
    ),
    ...Object.keys(c.outputs),
    "reconstruction/competition-entry/contract.json",
  ]);
  for (const name of names) {
    const out = path.join(dir, name);
    await mkdir(path.dirname(out), { recursive: true });
    await copyFile(path.join(APP, name), out);
  }
  const f = path.join(
      dir,
      "packages/frontend/src/components/leaderboard/entry/original-entry-row.tsx",
    ),
    text = await readFile(f, "utf8");
  assert.ok(text.includes("U.username ??"));
  await writeFile(f, text.replace("U.username ??", "U.username ||"));
  await assert.rejects(verifyCompetitionEntry(dir), /maintained AST differs/);
  await writeFile(f, text);
  const doc = path.join(dir, "reconstruction/competition-entry/contract.json");
  await writeFile(doc, JSON.stringify({ ...c, limits: [] }, null, 2) + "\n");
  await assert.rejects(verifyCompetitionEntry(dir), /source contract differs/);
});
test("test host fixtures pass retained full entry schema; invalid supplied PnL is rejected", async () => {
  const spec = JSON.parse(
      await readFile(path.join(APP, "contracts/developer.openapi.json")),
    ),
    schema =
      spec.paths["/competitions/{idOrSlug}"].get.responses["200"].content[
        "application/json"
      ].schema.properties.leaderboard.properties.entries.items;
  for (const { entry } of rows)
    assert.deepEqual(validateAgainstSchema(entry, schema, "$", spec), []);
  assert.ok(
    validateAgainstSchema(
      { ...rows[0].entry, pnlUsd: "1000" },
      schema,
      "$",
      spec,
    ).length,
  );
});
test("source-context selection is explicit; no arbitrary variant default", () => {
  assert.equal(squadVariants.length, 2);
  assert.equal(imageVariants.length, 3);
  assert.throws(() => createEntryHelpers({ Intl }), /Explicit reviewed/);
  assert.throws(
    () => createEntryHelpers({ ...contexts[0], imageVariant: "unknown" }),
    /Explicit reviewed/,
  );
});
for (const context of contexts)
  test(
    context.squadVariant.slice(0, 8) +
      "/" +
      context.imageVariant.slice(0, 8) +
      ": complete used identity/image/verification/currency helpers",
    () => {
      const h = createEntryHelpers(context);
      assert.equal(h.profileHref(wallet), "/profile/" + wallet);
      assert.equal(h.profileHref("a/b?c"), "/profile/a%2Fb%3Fc");
      assert.equal(h.profileHref(""), null);
      assert.equal(
        h.shortWallet(wallet),
        wallet.slice(0, 4) + "…" + wallet.slice(-4),
      );
      assert.equal(h.shortWallet("short"), "short");
      assert.equal(
        h.squadHref({ groupId: "a/b", username: "Valid_1" }),
        "/squads/Valid_1",
      );
      for (const username of ["create", "INVITATIONS", "bad-name", null])
        assert.equal(
          h.squadHref({ groupId: "a/b", username }),
          "/squads/a%2Fb",
        );
      assert.equal(
        h.normalizeImage("  https://fixture.invalid/a.png  "),
        "https://fixture.invalid/a.png",
      );
      assert.equal(h.normalizeImage("  "), undefined);
      assert.equal(h.normalizeImage(null), undefined);
      assert.equal(
        h.normalizeImage(
          "https://pump.mypinata.cloud/ipfs/QmeSzchzEPqCU1jwTnsipwcBAeH7S4bmVvFGfF65iA1BY1",
        ),
        undefined,
      );
      assert.equal(h.ipfsPrefix, "https://pump.mypinata.cloud/ipfs/");
      assert.equal(h.isVerified({ isVerified: true }), true);
      for (const value of [
        { isVerified: 1 },
        { isVerified: false },
        { isVerified: true, verifiedBadgeVisible: false },
      ])
        assert.equal(h.isVerified(value), false);
      assert.equal(h.formatPnl(1000), "$1,000.00");
      assert.equal(h.formatPnl(-25), "-$25.00");
      assert.equal(h.formatPnl(-0), "-$0.00");
      assert.equal(h.formatPnl(NaN), "$0.00");
      assert.equal(h.formatPnl(Infinity), "$0.00");
    },
  );
test("actual React SSR executes complete row and captured consumer; binds Avatar/Link props, SVGs, escaping and raw prize without mutating inputs", async (t) => {
  const temporary = await mkdtemp(
    path.join(APP, "packages/frontend", ".entry-ssr-"),
  );
  t.after(() => rm(temporary, { recursive: true, force: true }));
  const source = await readFile(
      path.join(
        APP,
        "packages/frontend/src/components/leaderboard/entry/original-entry-row.tsx",
      ),
      "utf8",
    ),
    compiled = await transform(source, {
      loader: "tsx",
      format: "cjs",
      jsx: "automatic",
    }),
    file = path.join(temporary, "row.cjs");
  await writeFile(file, compiled.code);
  const { createEntryRow } = createRequire(import.meta.url)(file);
  const before = JSON.stringify(rows);
  let avatars = [],
    links = [];
  const capabilities = {
    jsx,
    jsxs,
    React,
    useMemoCache,
    useTranslation: () => ({ t: syntheticTranslate }),
    classNames: (...parts) => parts.filter(Boolean).join(" "),
    Avatar: (props) => {
      avatars.push(props);
      return jsx("span", { "data-avatar": props.address });
    },
    Link: ({ href, prefetch, children, ...props }) => {
      links.push({ href, prefetch });
      return jsx("a", { href, ...props, children });
    },
  };
  for (const context of contexts) {
    avatars = [];
    links = [];
    const { EntryConsumer } = createEntryRow({
      ...capabilities,
      ...createEntryHelpers(context),
    });
    const html = renderToStaticMarkup(
      jsx("section", {
        children: rows.map((row) =>
          jsx(EntryConsumer, { row }, row.entry.entryId),
        ),
      }),
    );
    assert.ok(html.includes("+$1,000.00"));
    assert.ok(html.includes("-$25.00"));
    assert.ok(html.includes("fixture-members:3"));
    assert.ok(html.includes("fixture-anonymous"));
    assert.ok(html.includes("Verified account"));
    assert.ok(html.includes("cup-entry-prize"));
    assert.ok(html.includes("1000"));
    assert.ok(html.includes("–"));
    assert.deepEqual(
      links.map((x) => x.href),
      [
        "/profile/" + wallet,
        "/squads/group%2Ffixture",
        "/profile/anonymous-fixture",
        "/profile/unranked-fixture",
      ],
    );
    assert.ok(links.every((x) => x.prefetch === false));
    assert.equal(avatars[0].src, "https://fixture.invalid/avatar.png");
    assert.equal(avatars[0].width, 40);
    assert.equal(avatars[0].height, 40);
    assert.equal(avatars[0].isAnonymous, false);
    assert.equal(avatars[1].address, "group/fixture");
    assert.ok(avatars[1].className.includes("rounded-xl"));
    const unsafe = {
        entry: { ...rows[0].entry, username: "<img onerror='x'>" },
        prize: { rankFrom: 1, rankTo: 1, amount: "<b>prize</b>" },
      },
      escaped = renderToStaticMarkup(jsx(EntryConsumer, { row: unsafe }));
    assert.ok(escaped.includes("&lt;img"));
    assert.ok(escaped.includes("&lt;b&gt;prize&lt;/b&gt;"));
    assert.ok(!escaped.includes("<img"));
  }
  assert.equal(JSON.stringify(rows), before);
});
