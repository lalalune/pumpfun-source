import assert from "node:assert/strict";
import { test } from "node:test";
import {
  readFile,
  writeFile,
  mkdir,
  mkdtemp,
  rm,
  link,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import React from "../packages/frontend/node_modules/react/index.js";
import { jsx } from "../packages/frontend/node_modules/react/jsx-runtime.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import { verifyCompetitionBoard } from "../scripts/original-competition-board.mjs";
import {
  squadVariants,
  imageVariants,
} from "../packages/frontend/src/components/leaderboard/entry/entry-helpers.mjs";
import { prizeNumberVariants } from "../packages/frontend/src/components/leaderboard/original-prize-formats.mjs";
import {
  competition,
  entries,
  detail,
  buckets,
  translateBoard,
} from "./fixtures/competition-board-data.mjs";
import { selectCompetition } from "../reconstruction/competition-client/selection.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), ".."),
  sdk = createRequire(path.join(APP, "packages/sdk/package.json")),
  { build } = createRequire(sdk.resolve("tsup"))("esbuild");
async function makeFactory(t) {
  const dir = await mkdtemp(path.join(APP, "packages/frontend/.board-ssr-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const out = path.join(dir, "board.cjs");
  await build({
    entryPoints: [
      path.join(
        APP,
        "packages/frontend/src/components/leaderboard/board/CompetitionBoardDisplay.tsx",
      ),
    ],
    bundle: true,
    write: true,
    outfile: out,
    format: "cjs",
    platform: "node",
    jsx: "automatic",
    external: ["react", "react/jsx-runtime", "react/compiler-runtime"],
    nodePaths: [path.join(APP, "packages/frontend/node_modules")],
  });
  return createRequire(import.meta.url)(out).createCompetitionBoardComponents;
}
function caps({
  list = { data: buckets, isLoading: false, isError: false },
  read = { data: detail, isLoading: false, isError: false },
  reduced = false,
} = {}) {
  const calls = [],
    hero = [],
    highlight = [],
    rules = [];
  return {
    calls,
    hero,
    highlight,
    rules,
    options: {
      squadVariant: squadVariants[0].sha256,
      imageVariant: imageVariants[0].sha256,
      numberVariant: prizeNumberVariants[0].sha256,
      useTranslation: () => ({ t: translateBoard, i18n: { language: "en" } }),
      useSolPrice: () => ({ data: 100 }),
      useReducedMotion: () => reduced,
      Avatar: (p) => jsx("span", { "data-avatar": p.address }),
      Link: ({ children, prefetch, ...p }) => jsx("a", { ...p, children }),
      client: {
        useList: (o) => {
          calls.push(["list", o]);
          return { ...list, refetch: () => calls.push(["refetch-list"]) };
        },
        useDetail: (o) => {
          calls.push(["detail", o]);
          return { ...read, refetch: () => calls.push(["refetch-detail"]) };
        },
        selectCompetition,
      },
      Hero: (p) => {
        hero.push(p);
        return jsx("header", {
          "data-testid": "host-hero",
          children: p.competition?.title ?? "host-empty",
        });
      },
      Highlights: (p) => {
        highlight.push(p);
        return jsx("aside", {
          "data-testid": "host-highlights",
          "data-window": JSON.stringify(p.window),
        });
      },
      Rules: (p) => {
        rules.push(p);
        return null;
      },
      Card: ({ children, ariaLabel, testId }) =>
        jsx("section", {
          "aria-label": ariaLabel,
          "data-testid": testId,
          children,
        }),
    },
  };
}
test("full original board, two actual callers, predicates and typed component bodies authenticate against original bytes", async () => {
  const c = await verifyCompetitionBoard();
  assert.equal(c.source.selectedIndexEntries.length, 7);
  for (const label of [
    "COMPLETE actual competition-board coordinator to",
    "actual person board invocation and control placement",
    "actual group board invocation and control placement",
    "COMPLETE used paid-rank boundary function",
  ])
    assert.ok(
      c.witnesses.some((w) => w.label === label),
      label,
    );
  assert.equal(
    c.witnesses.filter((w) =>
      w.label.includes("unreconstructed compatible motion-card"),
    ).length,
    2,
  );
});
test("strict gate rejects planner behavior drift and independent source-receipt edits", async (t) => {
  const dir = await mkdtemp(path.join(APP, ".board-source-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const c = JSON.parse(
    await readFile(
      path.join(APP, "reconstruction/competition-board/contract.json"),
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
    "reconstruction/competition-board/contract.json",
  ]);
  for (const name of names) {
    const dest = path.join(dir, name);
    await mkdir(path.dirname(dest), { recursive: true });
    if (
      name.endsWith("original-board.tsx") ||
      name === "reconstruction/competition-board/contract.json"
    )
      await writeFile(dest, await readFile(path.join(APP, name)));
    else await link(path.join(APP, name), dest);
  }
  const f = path.join(dir, Object.keys(c.outputs)[0]),
    original = await readFile(f, "utf8");
  assert.ok(original.includes("s.rank === t"));
  await writeFile(f, original.replace("s.rank === t", "s.rank > t"));
  await assert.rejects(verifyCompetitionBoard(dir), /maintained AST differs/);
  await writeFile(f, original);
  await writeFile(
    path.join(dir, "reconstruction/competition-board/contract.json"),
    "{}\n",
  );
  await assert.rejects(verifyCompetitionBoard(dir), /source contract differs/);
});
test("actual React SSR composes real row/viewer/prize components in original order and preserves raw input; all six identity/image contexts and both NumberFormat contexts", async (t) => {
  const create = await makeFactory(t);
  for (const squad of squadVariants)
    for (const image of imageVariants)
      for (const number of prizeNumberVariants) {
        const state = caps();
        Object.assign(state.options, {
          squadVariant: squad.sha256,
          imageVariant: image.sha256,
          numberVariant: number.sha256,
        });
        const { PersonConsumer } = create(state.options),
          before = JSON.stringify({ competition, detail, buckets });
        const html = renderToStaticMarkup(
          jsx(PersonConsumer, {
            periodControl: jsx("button", { children: "host-period" }),
            periodControlTopPx: 42,
          }),
        );
        assert.deepEqual(state.calls, [
          ["list", { isVisible: true }],
          ["detail", { idOrSlug: competition.id, isVisible: true }],
        ]);
        assert.equal(state.hero[0].kind, "person");
        assert.equal(state.hero[0].topControlTopPx, 42);
        assert.equal(
          state.hero[0].className,
          "[--cup-lead:79px] sm:[--cup-lead:61px] lg:[--cup-lead:43px]",
        );
        assert.deepEqual(state.highlight[0].entries, entries);
        assert.deepEqual(state.highlight[0].window, {
          fromMs: Date.parse(competition.startsAt),
          toMs: Date.parse(competition.endsAt),
        });
        assert.equal(state.rules[0].open, false);
        const order = [
          "cup-rank-card",
          "fixture-standings",
          'data-entry-id="entry-1"',
          'data-entry-id="entry-2"',
          "cup-payline",
          'data-entry-id="entry-3"',
        ];
        for (let i = 1; i < order.length; i++)
          assert.ok(
            html.indexOf(order[i - 1]) < html.indexOf(order[i]),
            JSON.stringify(order),
          );
        assert.equal(
          (html.match(/data-testid="cup-entry-row"/g) || []).length,
          3,
        );
        assert.equal(
          (html.match(/data-testid="cup-entry-prize"/g) || []).length,
          2,
        );
        assert.ok(html.includes("fixture-paid-ranks:2"));
        assert.ok(html.includes("cup-board-in"));
        assert.equal(JSON.stringify({ competition, detail, buckets }), before);
      }
});
test("no competition keeps detail disabled at literal null and emits only hero; list state/refetch are forwarded", async (t) => {
  const create = await makeFactory(t),
    state = caps({
      list: { isLoading: true, isError: true },
      read: { isLoading: false, isError: false },
    }),
    { PersonConsumer } = create(state.options);
  const html = renderToStaticMarkup(jsx(PersonConsumer, {}));
  assert.deepEqual(state.calls[1], [
    "detail",
    { idOrSlug: null, isVisible: true },
  ]);
  assert.equal(state.hero[0].competition, null);
  assert.equal(state.hero[0].isLoading, true);
  assert.equal(state.hero[0].isError, true);
  state.hero[0].onRetry();
  assert.deepEqual(state.calls.at(-1), ["refetch-list"]);
  assert.ok(!html.includes("cup-board-below-hero"));
  assert.equal(state.rules.length, 0);
  assert.equal(state.highlight.length, 0);
});
test("live empty detail retains pending+viewer+prize tiers; ended empty/no-prize omits viewer and detail errors do not invent a new fallback", async (t) => {
  const create = await makeFactory(t),
    liveDetail = { ...detail, leaderboard: { entries: [] } },
    state = caps({
      read: { data: liveDetail, isLoading: false, isError: true },
      reduced: true,
    }),
    { PersonConsumer } = create(state.options);
  const html = renderToStaticMarkup(jsx(PersonConsumer, {}));
  for (const s of [
    "cup-pending",
    "cup-rank-card",
    "fixture-prize-breakdown",
    "cup-tier-1",
    "cup-tier-2",
  ])
    assert.ok(html.includes(s), s);
  assert.ok(!html.includes("cup-entry-row"));
  assert.ok(!html.includes("cup-board-in"));
  assert.equal(state.highlight.length, 0);
  const end = { ...competition, phase: "ended", prizes: [] },
    empty = caps({
      read: {
        data: { ...liveDetail, competition: end },
        isLoading: false,
        isError: true,
      },
    }),
    { PersonConsumer: E } = create(empty.options),
    endHtml = renderToStaticMarkup(jsx(E, {}));
  assert.ok(!endHtml.includes("cup-board-below-hero"));
  assert.ok(!endHtml.includes("cup-rank-card"));
  assert.equal(empty.hero[0].competition, end);
});
test("detail competition wins over list; final section and invalid/reversed date windows are preserved; actual group caller binds its own control class", async (t) => {
  const create = await makeFactory(t);
  for (const dates of [
    { startsAt: "bad", endsAt: competition.endsAt },
    { startsAt: competition.endsAt, endsAt: competition.startsAt },
    { startsAt: null, endsAt: null },
  ]) {
    const data = {
        ...detail,
        competition: {
          ...competition,
          ...dates,
          kind: "group",
          phase: "ended",
          title: "Detail title",
        },
      },
      state = caps({
        list: {
          data: { ...buckets, live: [{ ...competition, kind: "group" }] },
          isLoading: false,
          isError: false,
        },
        read: { data, isLoading: false, isError: false },
      }),
      { GroupConsumer } = create(state.options),
      html = renderToStaticMarkup(jsx(GroupConsumer, {}));
    assert.ok(html.includes("fixture-final-results"));
    assert.equal(state.hero[0].competition.title, "Detail title");
    assert.equal(state.hero[0].className, "[--cup-lead:8px]");
    assert.equal(state.hero[0].topControlTopPx, null);
    assert.equal(state.highlight[0].window, null);
    assert.equal(state.calls[1][1].idOrSlug, competition.id);
  }
});
