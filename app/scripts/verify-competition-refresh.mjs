import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import { buildCompetitionClient } from "./original-competition-client.mjs";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  sha256,
} from "./original-contracts/source.mjs";

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PAGE = "packages/frontend/src/app/leaderboard/leaderboard-client.tsx";
const LOOP = "packages/frontend/src/app/leaderboard/competition-refresh.ts";
const DIRECTORY = "reconstruction/competition-refresh";
const tail = (node) =>
  node.type === "SequenceExpression" ? node.expressions.at(-1) : node;
const ast = (text) =>
  parse(text, { sourceType: "module", plugins: ["typescript", "jsx"] });
function shape(node) {
  if (Array.isArray(node)) return node.map(shape);
  if (!node || typeof node !== "object") return node;
  return Object.fromEntries(
    Object.entries(node)
      .filter(
        ([k]) =>
          ![
            "start",
            "end",
            "loc",
            "extra",
            "comments",
            "leadingComments",
            "trailingComments",
            "innerComments",
            "typeAnnotation",
            "returnType",
          ].includes(k),
      )
      .map(([k, value]) => [k, shape(value)]),
  );
}
const expression = (text) => ast("(" + text + ")").program.body[0].expression;
const declaration = (tree, name) =>
  exactlyOne(
    findNodes(
      tree,
      (n) => n.type === "FunctionDeclaration" && n.id?.name === name,
    ),
    "actual " + name,
  );
const property = (node, name) =>
  exactlyOne(
    node.properties.filter(
      (n) =>
        n.type === "ObjectProperty" && (n.key.name ?? n.key.value) === name,
    ),
    "actual property " + name,
  ).value;
const returned = (fn) =>
  exactlyOne(
    fn.body.body.filter((n) => n.type === "ReturnStatement"),
    "actual function return",
  ).argument;
function originalHook(factory, id) {
  const registration = exactlyOne(
    findNodes(
      factory.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, factory.runtime, "s") &&
        (n.arguments[1]?.value === id ||
          (!n.arguments[1] && factory.ids.length === 1 && factory.id === id)),
    ),
    "actual selected module registration " + id,
  );
  const values = registration.arguments[0].elements;
  const found = [];
  for (let i = 0; i < values.length; i += 3)
    if (values[i].value === "f") found.push(values[i + 2]);
  return exactlyOne(found, "actual selected hook export " + id);
}

export async function verifyCompetitionRefresh(appRoot = APP) {
  const accepted = await buildCompetitionClient(appRoot);
  const corpus = await openCorpus(appRoot);
  const witnesses = [];
  const descriptors = {};
  for (const [id, name, ms, stale] of [
    [359516, "useList.mjs", 60000, 15000],
    [961415, "useDetail.mjs", 15000, 5000],
  ]) {
    const origin = accepted.contract.adapters.find(
      (row) => row.path === name,
    ).factory;
    const factory = await corpus.factory(id, { source: origin.source });
    const hook = originalHook(factory, id);
    const imported = exactlyOne(
      findNodes(
        factory.node,
        (n) =>
          n.type === "VariableDeclarator" &&
          n.init?.type === "CallExpression" &&
          member(n.init.callee, factory.runtime, "i") &&
          n.init.arguments[0]?.value === 85324,
      ),
      "actual foreground import " + id,
    );
    const interval = exactlyOne(
      findNodes(
        hook,
        (n) =>
          n.type === "CallExpression" &&
          member(tail(n.callee), imported.id.name, "q"),
      ),
      "actual foreground interval " + id,
    );
    assert.equal(interval.arguments[0].value, ms);
    const staleTime = exactlyOne(
      findNodes(
        hook,
        (n) => n.type === "ObjectProperty" && n.key?.name === "staleTime",
      ),
      "actual query staleTime " + id,
    );
    assert.equal(staleTime.value.value, stale);
    descriptors[name] = { intervalMs: ms, staleTimeMs: stale };
    witnesses.push(
      factory.witness(interval, "complete used interval call " + id),
      factory.witness(
        staleTime,
        "original cache descriptor; no native cache reconstruction " + id,
      ),
    );
  }
  const loopText = await readFile(path.join(appRoot, LOOP), "utf8");
  const tree = ast(loopText);
  const snapshot = returned(declaration(tree, "competitionIsForeground"));
  const expected = expression(
    '"visible" === document.visibilityState && document.hasFocus()',
  );
  assert.deepEqual(
    shape(snapshot),
    shape(expected),
    "native visible AND focused snapshot",
  );
  const variants = accepted.contract.adapters.filter((row) =>
    row.path.startsWith("foreground/"),
  );
  assert.equal(variants.length, 2);
  for (const variant of variants) {
    const factory = await corpus.factory(85324, {
      source: variant.factory.source,
    });
    const original = exactlyOne(
      findNodes(
        factory.node,
        (n) =>
          n.type === "ArrowFunctionExpression" &&
          n.body.type === "LogicalExpression" &&
          findNodes(
            n.body,
            (v) =>
              v.type === "CallExpression" &&
              member(v.callee, "document", "hasFocus"),
          ).length,
      ),
      "complete original foreground snapshot",
    );
    assert.deepEqual(
      shape(original.body),
      shape(snapshot),
      "both original variants share native snapshot",
    );
    witnesses.push(
      factory.witness(
        original,
        "same complete snapshot in both physical variants; no global winner selected",
      ),
    );
  }
  const interval = declaration(tree, "competitionRefreshInterval");
  assert.deepEqual(
    shape(returned(interval)),
    shape(
      expression(
        'category === "competitions" ? (competitionId ? 15000 : 60000) : false',
      ),
    ),
    "native used list/detail cadence",
  );
  const loop = declaration(tree, "startCompetitionReads");
  const eventCalls = (method) =>
    findNodes(
      loop,
      (n) =>
        n.type === "CallExpression" &&
        n.callee?.type === "MemberExpression" &&
        n.callee.property.name === method,
    ).map((n) => ({
      target: n.callee.object.property?.name,
      event: n.arguments[0]?.value,
      callback: n.arguments[1]?.name,
    }));
  const events = [
    {
      target: "document",
      event: "visibilitychange",
      callback: "foregroundChanged",
    },
    { target: "window", event: "focus", callback: "foregroundChanged" },
    { target: "window", event: "blur", callback: "foregroundChanged" },
  ];
  assert.deepEqual(
    eventCalls("addEventListener"),
    events,
    "actual subscription set",
  );
  assert.deepEqual(
    eventCalls("removeEventListener"),
    events,
    "same subscription cleanup",
  );

  const pageText = await readFile(path.join(appRoot, PAGE), "utf8");
  const page = ast(pageText);
  assert.equal(
    exactlyOne(
      findNodes(
        page,
        (n) =>
          n.type === "ImportDeclaration" &&
          n.source.value === "./competition-refresh",
      ),
      "used refresh import",
    ).specifiers.length,
    2,
  );
  const native = declaration(page, "LeaderboardClient");
  const setup = exactlyOne(
    findNodes(
      native,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.name === "useEffect" &&
        findNodes(
          n.arguments[0],
          (v) =>
            v.type === "CallExpression" &&
            v.callee.name === "startCompetitionReads",
        ).length,
    ),
    "actual native fetch effect",
  );
  const call = exactlyOne(
    setup.arguments[0].body.body.filter(
      (n) =>
        n.type === "ReturnStatement" &&
        n.argument?.callee?.name === "startCompetitionReads",
    ),
    "actual effect returns loop cleanup",
  ).argument;
  assert.deepEqual(
    shape(call.arguments[1]),
    shape(expression("competitionRefreshInterval(category, competitionId)")),
    "actual used query interval",
  );
  const read = call.arguments[0];
  assert.equal(read.type, "ArrowFunctionExpression");
  assert.equal(read.async, true);
  assert.equal(read.params[0].properties[0].key.name, "signal");
  const fetch = exactlyOne(
    findNodes(
      read,
      (n) => n.type === "CallExpression" && n.callee.name === "fetch",
    ),
    "actual native fetch",
  );
  assert.deepEqual(
    shape(fetch.arguments[0]),
    shape(expression("`/api/leaderboard?${apiQuery}`")),
    "existing actual adapter",
  );
  assert.equal(property(fetch.arguments[1], "method").value, "GET");
  assert.equal(
    property(fetch.arguments[1], "signal").name,
    "signal",
    "actual request abort signal",
  );
  assert.equal(
    findNodes(
      read,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.name === "parseLeaderboardResponse",
    ).length,
    1,
    "actual client admission retained",
  );
  assert.equal(
    findNodes(
      read,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.name === "setLoading" &&
        n.arguments[0]?.value === true,
    ).length,
    0,
    "background reads do not clear loaded UI",
  );
  const contract = {
    schema: 1,
    reusedAcceptedUnit: 868,
    acceptedClientContractSha256: sha256(JSON.stringify(accepted.contract)),
    originalDescriptors: descriptors,
    originalConsumers: accepted.contract.consumers,
    actualConsumerCalls: accepted.contract.witnesses.filter((w) =>
      /^actual consumer 590407 (import|call)/.test(w.label),
    ),
    originalWitnesses: witnesses,
    native: {
      page: PAGE,
      loop: LOOP,
      loopSha256: sha256(loopText),
      foregroundAstSha256: sha256(JSON.stringify(shape(snapshot))),
      usedEffectSha256: sha256(pageText.slice(setup.start, setup.end)),
    },
    unchangedAdmission: Object.fromEntries(
      await Promise.all(
        [
          "packages/frontend/src/app/api/leaderboard/route.ts",
          "packages/frontend/src/app/api/leaderboard/upstream.ts",
          "packages/frontend/src/app/leaderboard/types.ts",
        ].map(async (file) => [
          file,
          sha256(await readFile(path.join(appRoot, file))),
        ]),
      ),
    ),
    limits: [
      "Exact original interval/snapshot/caller attribution reuses accepted868, with no new factory recovery count.",
      "Original query-provider cache, staleTime scheduling, viewer scope, null-only disabled projection and focus/refetch defaults are not implemented by this native scheduling port.",
      "Initial native reads remain unconditional; native parameter admission stays with the existing actual adapter. Only recurring competition reads are foreground-gated.",
      "Completion-relative local scheduling avoids overlaps; controls/data are retained until an admitted response or fail-closed error. No original query-runtime or production API/provider/auth parity claim.",
    ],
  };
  return contract;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const contract = await verifyCompetitionRefresh();
  const dest = path.join(APP, DIRECTORY, "contract.json");
  if (process.argv[2] === "--write") {
    await mkdir(path.dirname(dest), { recursive: true });
    await writeFile(dest, JSON.stringify(contract, null, 2) + "\n");
  } else {
    assert.equal(process.argv[2], "--check");
    assert.equal(
      await readFile(dest, "utf8"),
      JSON.stringify(contract, null, 2) + "\n",
      "source contract changed",
    );
  }
  console.log(
    "Verified original competition polling/caller closure and actual native request/admission/cleanup binding; query cache remains an explicit boundary",
  );
}
