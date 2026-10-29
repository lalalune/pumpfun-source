import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile, mkdtemp, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import React from "../packages/frontend/node_modules/react/index.js";
import { jsx } from "../packages/frontend/node_modules/react/jsx-runtime.js";
import { renderToStaticMarkup } from "../packages/frontend/node_modules/react-dom/server.node.js";
import { verifyProfileLink } from "../scripts/original-profile-link.mjs";
import {
  createProfileLinkModule,
  profileRoute,
  useMemoCache,
} from "../packages/frontend/src/components/leaderboard/original-profile-link.mjs";
import { isOrdinaryClick } from "../packages/frontend/src/components/leaderboard/original-profile-click.mjs";
import { startProfileLinkHttp } from "./fixtures/profile-link-http.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sdk = createRequire(path.join(APP, "packages/sdk/package.json"));
const { build } = createRequire(sdk.resolve("tsup"))("esbuild");
async function compile(t, entry, exposeRow = false) {
  const dir = await mkdtemp(path.join(APP, "packages/frontend/.profile-link-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const out = path.join(dir, "actual.cjs");
  await build({
    entryPoints: [path.join(APP, entry)],
    outfile: out,
    bundle: true,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    external: ["react", "react/*", "next/*"],
    plugins: [
      {
        name: "test-only-actual-exports",
        setup(b) {
          b.onResolve({ filter: /^server-only$/ }, () => ({
            path: "server-only",
            namespace: "empty",
          }));
          b.onLoad({ filter: /.*/, namespace: "empty" }, () => ({
            contents: "",
            loader: "js",
          }));
          if (exposeRow)
            b.onLoad({ filter: /leaderboard-client\.tsx$/ }, async (args) => ({
              contents:
                (await readFile(args.path, "utf8")) + "\nexport {TraderRows};",
              loader: "tsx",
            }));
        },
      },
    ],
  });
  return createRequire(import.meta.url)(out);
}
const front = "packages/frontend/src/";
const component = front + "components/leaderboard/";
const wallet = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU";
const local = {
  walletAddress: wallet,
  userId: "user-001",
  username: "alice_pump",
};
function sourceRender(props = {}, navigation) {
  let observed;
  const Link = (values) => {
    observed = values;
    const { prefetch, ...anchor } = values;
    return jsx("a", anchor);
  };
  const module = createProfileLinkModule({
    jsx,
    useMemoCache,
    useContext: React.useContext,
    createContext: React.createContext,
    Link,
    profileRoute,
    isOrdinaryClick,
    classNames: (...v) => v.filter(Boolean).join(" "),
  });
  let tree = jsx(module.ProfileLink, {
    profileId: wallet,
    children: "Alice",
    ...props,
  });
  if (navigation !== undefined)
    tree = jsx(module.ProfileNavigationProvider, {
      value: navigation,
      children: tree,
    });
  return {
    html: renderToStaticMarkup(tree),
    get props() {
      return observed;
    },
  };
}
const event = (extra = {}) => ({
  button: 0,
  metaKey: false,
  ctrlKey: false,
  shiftKey: false,
  altKey: false,
  defaultPrevented: false,
  preventDefault() {
    this.defaultPrevented = true;
  },
  ...extra,
});
test("both complete physical components and actual trader consumers are source-bound", async () => {
  const contract = await verifyProfileLink();
  assert.equal(
    contract.commonCompleteComponentAstSha256,
    "1cefef53dec5db2a4829c4d049508ca4f8a9b0e44977f1c56130df3660f626ca",
  );
  assert.equal(contract.consumers.length, 2);
  assert.ok(contract.witnesses.every((w) => w.sha256 && w.utf8 && w.utf16));
});
test("real React/compiler SSR with null context preserves URL, children, rest props and no pending state", () => {
  const r = sourceRender({
    className: "base",
    title: "Local example",
    prefetch: false,
  });
  assert.ok(r.html.includes('href="/profile/' + wallet + '"'));
  assert.ok(r.html.includes("Alice"));
  assert.equal(r.props["aria-busy"], undefined);
  assert.equal(r.props.title, "Local example");
  assert.equal(r.props.prefetch, false);
  const e = event();
  r.props.onClick(e);
  assert.equal(e.defaultPrevented, false);
});
test("accepted profileRoute and original override semantics retain exact encoding/null behavior", () => {
  assert.equal(
    profileRoute({ address: " a/b ", userId: "ignored" }),
    "/profile/a%2Fb",
  );
  assert.equal(
    profileRoute({ address: " ", userId: " id?x " }),
    "/profile/id%3Fx",
  );
  assert.equal(profileRoute(" a/b "), "/profile/%20a%2Fb%20");
  assert.equal(profileRoute(null), null);
  assert.equal(sourceRender({ href: "/explicit" }).props.href, "/explicit");
  assert.equal(sourceRender({ href: "" }).props.href, "");
});
test("explicit UI context preserves callback-before-provider order, identity pending and class port", () => {
  const calls = [];
  const r = sourceRender(
    { className: "base", onClick: () => calls.push("caller") },
    { pendingProfileId: wallet, navigateToProfile: (id) => calls.push(id) },
  );
  const e = event();
  r.props.onClick(e);
  assert.deepEqual(calls, ["caller", wallet]);
  assert.equal(e.defaultPrevented, true);
  assert.equal(r.props["aria-busy"], true);
  assert.equal(r.props.className, "base cursor-progress opacity-60");
});
test("canceled/modifier/non-left clicks never invoke UI context navigation", () => {
  const calls = [];
  const r = sourceRender(
    {
      onClick: (e) => {
        if (e.button === 2) e.preventDefault();
      },
    },
    { pendingProfileId: "other", navigateToProfile: (id) => calls.push(id) },
  );
  for (const extra of [
    { button: 1 },
    { button: 2 },
    { metaKey: true },
    { ctrlKey: true },
    { shiftKey: true },
    { altKey: true },
    { defaultPrevented: true },
  ]) {
    const e = event(extra);
    assert.equal(isOrdinaryClick(e), false);
    r.props.onClick(e);
  }
  assert.deepEqual(calls, []);
  assert.equal(r.props["aria-busy"], undefined);
});
test("falsy identifier bypasses context navigation and supplied callback can cancel first", () => {
  const calls = [];
  const navigation = {
    pendingProfileId: wallet,
    navigateToProfile: (id) => calls.push(id),
  };
  const canceled = sourceRender(
    { onClick: (e) => e.preventDefault() },
    navigation,
  );
  canceled.props.onClick(event());
  const empty = sourceRender(
    { profileId: null, href: "/explicit" },
    navigation,
  );
  empty.props.onClick(event());
  assert.deepEqual(calls, []);
});
test("directory loads the existing hash-bound person records and excludes groups", async (t) => {
  const { loadLocalRankingProfiles } = await compile(
    t,
    component + "local-profile-directory.ts",
  );
  const read = (name) =>
    readFile(path.join(APP, "packages/backend/src/" + name + "-seed.json"));
  const records = await loadLocalRankingProfiles(read);
  assert.equal(records.length, 4);
  assert.ok(records.some((r) => JSON.stringify(r) === JSON.stringify(local)));
  assert.ok(!records.some((r) => r.userId === "user-004"));
  assert.ok(
    records.every(
      (r) => Object.keys(r).join(",") === "walletAddress,userId,username",
    ),
  );
});
test("corrupt, unavailable or non-pinned directory input fails closed without changing seed files", async (t) => {
  const { loadLocalRankingProfiles } = await compile(
    t,
    component + "local-profile-directory.ts",
  );
  assert.deepEqual(
    await loadLocalRankingProfiles(async () => new TextEncoder().encode("[]")),
    [],
  );
  assert.deepEqual(
    await loadLocalRankingProfiles(async () => {
      throw Error("unavailable");
    }),
    [],
  );
});
test("identity matching requires all three fields, valid exact address, and a known directory", async (t) => {
  const { matchingLocalRankingProfile: match } = await compile(
    t,
    component + "local-profile-identity.ts",
  );
  assert.equal(match(local, [local]), wallet);
  for (const row of [
    { ...local, userId: null },
    { ...local, username: "other" },
    { ...local, walletAddress: "/bad" },
    { ...local, walletAddress: wallet + " " },
  ])
    assert.equal(match(row, [local]), null);
  assert.equal(match(local, []), null);
});
test("actual native row uses recovered link only for known exact tuple while keeping supplied metrics", async (t) => {
  const { TraderRows } = await compile(
    t,
    front + "app/leaderboard/leaderboard-client.tsx",
    true,
  );
  const common = {
    rank: 1,
    pnlUsd: 100,
    pnlPercent: 10,
    realizedPnlUsd: -20,
    unrealizedPnlUsd: 120,
    positionsCount: 0,
    isVerified: true,
    verifiedBadgeVisible: true,
  };
  const entries = [
    { ...common, ...local },
    { ...common, rank: 2, ...local, userId: null },
    {
      ...common,
      rank: 3,
      ...local,
      walletAddress: "11111111111111111111111111111112",
      username: null,
      userId: null,
    },
  ];
  const html = renderToStaticMarkup(
    jsx(TraderRows, { entries, localProfiles: [local] }),
  );
  assert.equal((html.match(/<a /g) || []).length, 1);
  assert.ok(html.includes('href="/profile/' + wallet + '"'));
  assert.ok(html.includes("View local example profile for @alice_pump"));
  assert.equal((html.match(/\$100\.00/g) || []).length, 3);
  assert.equal(
    (html.replaceAll("<!-- -->", "").match(/Realized -\$20\.00/g) || []).length,
    3,
  );
  assert.ok(html.includes("Verified profile"));
});
test("actual native HTTP identity hydration and existing adapter retain key/error/retry boundaries", async (t) => {
  const fixture = await startProfileLinkHttp();
  t.after(() => fixture.close());
  const url = fixture.backendUrl + "/v1/pnl-leaderboard?period=daily";
  assert.equal((await fetch(url)).status, 401);
  const admitted = await fetch(
    fixture.adapterUrl +
      "/api/leaderboard?category=traders&period=daily&sort=combined",
  );
  assert.equal(admitted.status, 200);
  const body = await admitted.json();
  assert.equal(body.ok, true);
  assert.deepEqual(
    Object.fromEntries(
      Object.keys(local).map((key) => [key, body.data.entries[0][key]]),
    ),
    local,
  );
  assert.equal(body.data.entries[1].username, "alice_pump");
  assert.notEqual(body.data.entries[1].walletAddress, wallet);
  const ledger = await fixture.command("snapshot");
  assert.ok(ledger.ledger.some((row) => row.keyMatched && row.status === 200));
  await fixture.command("stop-backend");
  assert.equal(
    (await fetch(fixture.adapterUrl + "/api/leaderboard?category=traders"))
      .status,
    502,
  );
  await fixture.command("start-backend");
  assert.equal(
    (await fetch(fixture.adapterUrl + "/api/leaderboard?category=traders"))
      .status,
    200,
  );
});
