import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { createServer } from "node:http";
import { once } from "node:events";
import {
  viewerFollowingKey,
  parseViewerFollowingText,
  requireViewerFollowingResponse,
  viewerFollowingQueryOptions,
  viewerFollowingSet,
  activeViewerFollowingOptions,
  passiveViewerFollowingOptions,
  viewerFollowingState,
  passiveFollowingMembership,
} from "../reconstruction/viewer-following/client.mjs";
import { UserFetchError } from "../reconstruction/profile-lookup/client.mjs";
import { extractViewerFollowing } from "../scripts/original-viewer-following.mjs";
import { openCorpus, sha256 } from "../scripts/original-contracts/source.mjs";
import { validateDeclared } from "../scripts/original-contracts/validate.mjs";
import {
  ContractError,
  withContractErrorNormalization,
} from "../reconstruction/contract-http-errors/decode.mjs";
const root = fileURLToPath(new URL("..", import.meta.url)),
  artifact = await extractViewerFollowing(root),
  corpus = await openCorpus(root);

test("actual303599 exports and shell/Home/button consumers bind passive membership to initial button state", () => {
  assert.equal(artifact.entry.module, 303599);
  assert.deepEqual(artifact.entry.exports, ["Q", "j", "G", "o"]);
  assert.deepEqual(
    artifact.consumers.map((x) => [x.module, x.calledExport]),
    [
      [400466, "Q"],
      [163807, "o"],
      [949060, "G"],
    ],
  );
  assert.ok(artifact.consumers[2].buttonProps);
  assert.equal(artifact.policy.limit, 1000);
  assert.equal(artifact.prerequisite.novelCredit, false);
});

test("source/adapter/dependency hashes and all original byte ranges reproduce", async () => {
  assert.equal(
    await fs.readFile(
      path.join(root, "reconstruction/viewer-following/contract.json"),
      "utf8",
    ),
    JSON.stringify(artifact, null, 2) + "\n",
  );
  for (const fragment of artifact.fragments) {
    const c = await corpus.capture(fragment.source);
    assert.equal(sha256(c.bytes.subarray(...fragment.utf8)), fragment.sha256);
    assert.equal(c.text.slice(...fragment.utf16), fragment.text);
  }
  for (const x of [artifact.implementation, artifact.prerequisite])
    assert.equal(sha256(await fs.readFile(path.join(root, x.path))), x.sha256);
});

test("modified viewer-following capture fails closed", async (t) => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), "viewer-following-"));
  t.after(() => fs.rm(dir, { recursive: true, force: true }));
  for (const name of [
    "evidence/web/manifest.json",
    "recovered/modules.json",
    artifact.entry.factory.source,
  ]) {
    const p = path.join(dir, name);
    await fs.mkdir(path.dirname(p), { recursive: true });
    await fs.copyFile(path.join(root, name), p);
  }
  const p = path.join(dir, artifact.entry.factory.source),
    bytes = await fs.readFile(p);
  bytes[100] ^= 1;
  await fs.writeFile(p, bytes);
  await assert.rejects(
    extractViewerFollowing(dir),
    /capture authentication failed/,
  );
});

test("strict outer-array parser preserves rows but classifies invalidJSON/shape without accepting users wrapper", () => {
  assert.deepEqual(parseViewerFollowingText('[null,{"unknown":true},3]'), [
    null,
    { unknown: true },
    3,
  ]);
  for (const text of ["", " ", "not JSON"])
    assert.throws(
      () => parseViewerFollowingText(text),
      (e) => e instanceof UserFetchError && e.reason === "invalid_json",
    );
  for (const text of ["null", "{}", '{"users":[]}', "true"])
    assert.throws(
      () => parseViewerFollowingText(text),
      (e) => e instanceof UserFetchError && e.reason === "invalid_shape",
    );
});

test("non-OK hook stays plainError while successful blank body is typed; cloned body remains readable", async () => {
  await assert.rejects(
    requireViewerFollowingResponse(null, null, {
      ok: false,
      status: 503,
      clone() {
        assert.fail();
      },
    }),
    (e) =>
      e.message === "Failed to fetch viewer following list: 503" &&
      !(e instanceof UserFetchError) &&
      !Object.hasOwn(e, "response"),
  );
  await assert.rejects(
    requireViewerFollowingResponse(null, null, new Response(" \n")),
    (e) => e instanceof UserFetchError && e.reason === "empty_body",
  );
  const response = new Response("[]");
  await requireViewerFollowingResponse(null, null, response);
  assert.equal(response.bodyUsed, false);
  assert.deepEqual(await response.json(), []);
});

test("Q preserves capped raw GET, signal, fresh option containers and raw cache-key values", async () => {
  const seen = [],
    raw = [{ user_id: "legacy", arbitrary: true }],
    signal = new AbortController().signal;
  const q = viewerFollowingQueryOptions(async (...args) => {
    seen.push(args);
    return raw;
  }, "Viewer");
  assert.deepEqual(q.queryKey, ["viewer-following", "Viewer"]);
  assert.equal(q.staleTime, 60000);
  assert.equal(q.gcTime, 300000);
  assert.equal(await q.queryFn({ signal }), raw);
  assert.deepEqual(seen[0], [
    "GET /following/v3/following/{userId}",
    {
      params: { userId: "Viewer" },
      query: { limit: 1000 },
      signal,
      throwHttpErrors: false,
      hooks: { afterResponse: [requireViewerFollowingResponse] },
      parseJson: parseViewerFollowingText,
    },
  ]);
  for (const key of ["credentials", "headers", "offset", "retry"])
    assert.equal(Object.hasOwn(seen[0][1], key), false);
  seen[0][1].query.limit = 1;
  await q.queryFn({ signal });
  assert.equal(seen[1][1].query.limit, 1000);
  assert.deepEqual(viewerFollowingKey(null), ["viewer-following", null]);
  assert.deepEqual(viewerFollowingKey(undefined), [
    "viewer-following",
    undefined,
  ]);
  assert.equal(q.refetchOnWindowFocus({ state: { status: "error" } }), true);
  assert.equal(q.refetchOnWindowFocus({ state: { status: "success" } }), false);
});

test("falsy viewer skips HTTP with valid query context; missing context still fails; posttransport null alone is guarded", async () => {
  const q = viewerFollowingQueryOptions(() => assert.fail(), null);
  assert.deepEqual(await q.queryFn({}), []);
  await assert.rejects(q.queryFn(), TypeError);
  await assert.rejects(
    viewerFollowingQueryOptions(async () => null, "viewer").queryFn({}),
    (e) => e instanceof UserFetchError && e.reason === "invalid_shape",
  );
  assert.equal(
    await viewerFollowingQueryOptions(async () => undefined, "viewer").queryFn(
      {},
    ),
    undefined,
  );
});

test("Set folds case without trim, preserves legacyuser_id nullish priority and ignores nonstring identities", () => {
  const values = viewerFollowingSet([
    { address: "Wallet", user_id: "Legacy", userId: "ignored" },
    { address: "WALLET", user_id: "", userId: "also-ignored" },
    { user_id: null, userId: "Current" },
    { address: 1, user_id: 0, userId: "suppressed" },
    { address: " spaced " },
    null,
  ]);
  assert.deepEqual([...values], ["wallet", "legacy", "current", " spaced "]);
  assert.equal(values.has("spaced"), false);
  assert.equal(values.has("ignored"), false);
  assert.deepEqual([...viewerFollowingSet(undefined)], []);
  assert.throws(() => viewerFollowingSet({ rows: [] }), TypeError);
});

test("active enablement and passive enabled:false differ while sharing same cache key", () => {
  const transport = () => assert.fail();
  const active = activeViewerFollowingOptions(transport, "viewer"),
    passive = passiveViewerFollowingOptions(transport, "viewer");
  assert.equal(active.enabled, true);
  assert.equal(passive.enabled, false);
  assert.deepEqual(active.queryKey, passive.queryKey);
  assert.equal(
    activeViewerFollowingOptions(transport, "viewer", { enabled: false })
      .enabled,
    false,
  );
  assert.equal(
    activeViewerFollowingOptions(transport, "viewer", { enabled: null })
      .enabled,
    true,
  );
  assert.equal(activeViewerFollowingOptions(transport, null).enabled, false);
});

test("active membership returns undefined until ready, then knowntrue/false; passive observes successful cache even disabled", () => {
  const query = {
    data: [{ address: "Wallet", user_id: "CC" }],
    isSuccess: true,
    isError: false,
  };
  let state = viewerFollowingState("viewer", undefined, query);
  assert.equal(state.ready, true);
  assert.equal(state.isError, false);
  assert.equal(state.isFollowing("WALLET"), true);
  assert.equal(state.isFollowing("cc"), true);
  assert.equal(state.isFollowing("missing"), false);
  assert.equal(state.isFollowing(""), undefined);
  state.followingSet.add("later");
  assert.equal(state.isFollowing("later"), true);
  state = viewerFollowingState("viewer", { enabled: false }, query);
  assert.equal(state.ready, false);
  assert.equal(state.isFollowing("wallet"), undefined);
  assert.equal(passiveFollowingMembership("viewer", "wallet", query), true);
  for (const q of [
    { ...query, isSuccess: false, isError: true },
    { data: undefined },
  ]) {
    assert.equal(
      viewerFollowingState("viewer", undefined, q).isFollowing("wallet"),
      undefined,
    );
    assert.equal(passiveFollowingMembership("viewer", "wallet", q), undefined);
  }
  assert.equal(passiveFollowingMembership(null, "wallet", query), undefined);
  assert.equal(passiveFollowingMembership("viewer", "", query), undefined);
});

test("error flag/stale set remain observable while unready; invalid cached row shape is not silently made empty", () => {
  const state = viewerFollowingState("viewer", undefined, {
    data: [{ address: "old" }],
    isSuccess: false,
    isError: true,
  });
  assert.equal(state.isError, true);
  assert.equal(state.followingSet.has("old"), true);
  assert.equal(state.isFollowing("old"), undefined);
  assert.throws(
    () => passiveFollowingMembership(null, null, { data: {} }),
    TypeError,
  );
  assert.throws(
    () => viewerFollowingState(null, undefined, { data: {} }),
    TypeError,
  );
});

function localTransport(origin, observations) {
  return async (operation, opts) =>
    withContractErrorNormalization(
      operation,
      async () => {
        observations.push(opts);
        const url = new URL(
          `${origin}/following/v3/following/${encodeURIComponent(String(opts.params.userId))}`,
        );
        url.searchParams.set("limit", String(opts.query.limit));
        const response = await fetch(url, { signal: opts.signal });
        for (const hook of opts.hooks.afterResponse)
          await hook(null, opts, response);
        return opts.parseJson(await response.text());
      },
      {
        contracts: {},
        routeErrorSchema: () => undefined,
        contractErrorBody: { safeParse: () => ({ success: false }) },
      },
    );
}
async function serverFor(t, handler) {
  const server = createServer(handler);
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(() => {
    server.closeAllConnections();
    server.close();
  });
  return `http://127.0.0.1:${server.address().port}`;
}

test("real HTTP: capped encoded viewer read projects active/passive known membership with legacy IDs", async (t) => {
  const requests = [],
    rows = [{ address: "Wallet", user_id: "Legacy", extra: true }],
    seen = [];
  const origin = await serverFor(t, (req, res) => {
    requests.push(req.url);
    res.end(JSON.stringify(rows));
  });
  const q = activeViewerFollowingOptions(
      localTransport(origin, seen),
      "viewer/slash ?",
    ),
    data = await q.queryFn({});
  assert.deepEqual(data, rows);
  assert.deepEqual(requests, [
    "/following/v3/following/viewer%2Fslash%20%3F?limit=1000",
  ]);
  const state = viewerFollowingState("viewer/slash ?", undefined, {
    data,
    isSuccess: true,
  });
  assert.equal(state.isFollowing("legacy"), true);
  assert.equal(state.isFollowing("absent"), false);
  assert.equal(
    passiveFollowingMembership("viewer/slash ?", "WALLET", {
      data,
      isSuccess: true,
    }),
    true,
  );
  assert.equal(Object.hasOwn(seen[0], "credentials"), false);
});

test("real HTTP: statusplainError, blankbody, malformedJSON and nonarray shapes remain distinct", async (t) => {
  const cases = {
    missing: [404, "not JSON"],
    unavailable: [503, "not JSON"],
    blank: [200, " \n"],
    invalid: [200, "not JSON"],
    shape: [200, '{"users":[]}'],
  };
  const origin = await serverFor(t, (req, res) => {
    const id = req.url.split("/").at(-1).split("?")[0],
      [status, body] = cases[id];
    res.writeHead(status);
    res.end(body);
  });
  const transport = localTransport(origin, []);
  for (const id of ["missing", "unavailable"])
    await assert.rejects(
      viewerFollowingQueryOptions(transport, id).queryFn({}),
      (e) =>
        e.message ===
          `Failed to fetch viewer following list: ${cases[id][0]}` &&
        !(e instanceof UserFetchError) &&
        !(e instanceof ContractError),
    );
  for (const [id, reason] of [
    ["blank", "empty_body"],
    ["invalid", "invalid_json"],
    ["shape", "invalid_shape"],
  ])
    await assert.rejects(
      viewerFollowingQueryOptions(transport, id).queryFn({}),
      (e) => e instanceof UserFetchError && e.reason === reason,
    );
});

test("real HTTP: exact signal cancellation propagates without converting unknown membership to false", async (t) => {
  let reached;
  const ready = new Promise((resolve) => {
    reached = resolve;
  });
  const origin = await serverFor(t, () => reached()),
    controller = new AbortController(),
    reason = Error("cancel local graph");
  const pending = assert.rejects(
    viewerFollowingQueryOptions(localTransport(origin, []), "viewer").queryFn({
      signal: controller.signal,
    }),
    (e) => e === reason,
  );
  await ready;
  controller.abort(reason);
  await pending;
  assert.equal(
    viewerFollowingState("viewer", undefined, {
      isError: true,
      isSuccess: false,
    }).isFollowing("target"),
    undefined,
  );
});

test("declared row schema remains separate from outer-array parser and capped Set completeness", () => {
  const doc = artifact.declarations,
    route = doc["x-viewer-following"];
  assert.equal(route.scope, "graph.read");
  assert.equal(
    validateDeclared(doc, route.params, { userId: "viewer" }).success,
    true,
  );
  assert.equal(validateDeclared(doc, route.response, [null]).success, false);
  assert.deepEqual(parseViewerFollowingText("[null]"), [null]);
  assert.match(artifact.policy.pagination, /no complete graph/);
});
