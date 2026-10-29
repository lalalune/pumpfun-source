// Static source authentication and AST/Flight JSON extraction; never evaluates captures.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  objectProperty,
  sha256,
} from "./original-contracts/source.mjs";
const rootDefault = fileURLToPath(new URL("..", import.meta.url));
const output = "reconstruction/relative-time/contract.json";
const demand = (condition, message) => {
  if (!condition) throw Error(`Relative time: ${message}`);
};
const tail = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function exportsOf(f, id = f.id) {
  const call = exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, f.runtime, "s") &&
        (n.arguments[1]?.value === id ||
          (n.arguments.length === 1 && f.ids.length === 1)),
    ),
    `actual export registration ${id}`,
  );
  const result = new Map(),
    values = call.arguments[0].elements;
  for (let i = 0; i < values.length; i += 3) {
    demand(
      values[i]?.type === "StringLiteral" &&
        values[i + 1]?.value === 0 &&
        !result.has(values[i].value),
      "unsupported exports",
    );
    result.set(values[i].value, values[i + 2]);
  }
  return result;
}
function resolve(f, node) {
  if (node?.type !== "Identifier") return node;
  const definitions = f.node.body.body.flatMap((s) =>
    s.type === "VariableDeclaration"
      ? s.declarations
      : s.type === "FunctionDeclaration"
        ? [s]
        : [],
  );
  const d = exactlyOne(
    definitions.filter((d) => d.id?.name === node.name),
    `top-level ${node.name}`,
  );
  return d.type === "FunctionDeclaration" ? d : d.init;
}
function binding(f, id) {
  return exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        ["i", "r"].some((m) => member(n.init.callee, f.runtime, m)) &&
        n.init.arguments[0]?.value === id,
    ),
    `import ${id}`,
  ).id.name;
}
function calls(node, alias, name) {
  return findNodes(
    node,
    (n) => n.type === "CallExpression" && member(tail(n.callee), alias, name),
  );
}
const specs = [
  [
    204478,
    "evidence/web/objects/2560599a20517277.js",
    "27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f",
  ],
  [
    529841,
    "evidence/web/objects/f4e16ef1b0b97d5e.js",
    "2c48084aa599d13dd584db59b0f98aaff7553849ceca936596d1063b20ded266",
  ],
  [
    632817,
    "evidence/web/objects/f4e16ef1b0b97d5e.js",
    "52e781c3edc1a9ee943d54965899aa850642bd5944553ffe8c23ef71c3dfb5ff",
  ],
  [
    668487,
    "evidence/web/objects/1e479323ffe53c14.js",
    "252bb240dc397f899066aa312ace869e02321f3e28aecd7134758ff33a0ff408",
  ],
  [
    633311,
    "evidence/web/objects/f4e16ef1b0b97d5e.js",
    "791665a66d45f129d6c31e0e1f0a79b0a24e8b95904ddee3c559fafca0cade40",
  ],
  [
    890088,
    "evidence/web/objects/994c0030bcc62017.js",
    "b6933f856a7fe6205483d9adca13b97117fed3fc3822f1383ed3ba99e512040b",
  ],
  [
    890088,
    "evidence/web/objects/7128bd47b219d222.js",
    "f29f27e66af25973af60575b0ffea4e03a9fc939855c0ff7d4a8f3c02d448e09",
  ],
  [
    187611,
    "evidence/web/objects/a0ec47219f76f808.js",
    "bd62a3ae8bc3cb897b656e246f762a897468e49c9752cfbe9e82f51de8397c3b",
  ],
  [
    170450,
    "evidence/web/objects/994c0030bcc62017.js",
    "72a61a3e662f4e2995ea53610e55b0658ec866cf82ddca6c904962252fe06ff7",
  ],
  [
    592209,
    "evidence/web/objects/a0ec47219f76f808.js",
    "6b3fe2082dbaa30d9d803777d25ef02aa53ccc736b312980dec097206324c790",
  ],
];
export async function recoverRelativeTime(root = rootDefault) {
  const corpus = await openCorpus(root);
  demand(
    corpus.anchors.manifestSha256 ===
      "9e0fc00719eb8c919dd4205d3c118eb48c4927e056c77e8343e26d6f7189bbb5",
    "unreviewed manifest",
  );
  demand(
    corpus.anchors.inventorySha256 ===
      "1d268ae7f2eb0f61eaaffd222269bf29d9ce06e9946372861721b2f159d868e2",
    "unreviewed inventory",
  );
  const factories = [];
  for (const [id, source, hash] of specs) {
    const f = await corpus.factory(id, { source });
    demand(f.provenance.sha256 === hash, `unreviewed factory ${id}`);
    factories.push(f);
  }
  const factory = (id) =>
    exactlyOne(
      factories.filter((f) => f.id === id),
      `factory ${id}`,
    );
  const fragments = [],
    add = (f, node, label, text = true) => {
      const w = f.witness(node, label);
      fragments.push({ ...w, ...(text ? { text: f.text(node) } : {}) });
      return w;
    };
  for (const id of [529841, 632817, 668487, 633311, 170450, 187611]) {
    const f = factory(id);
    add(f, f.node, `complete used source context ${id}`);
  }
  const renderer = factory(529841),
    component = resolve(renderer, exportsOf(renderer).get("f"));
  demand(
    component?.type === "FunctionExpression",
    "relative-time component export changed",
  );
  demand(
    calls(component, binding(renderer, 632817), "H").length === 1,
    "actual shared clock hook missing",
  );
  demand(
    calls(component, binding(renderer, 633311), "l").length === 1,
    "actual timestamp parser missing",
  );
  for (const name of ["f", "K", "V"])
    demand(
      calls(component, binding(renderer, 890088), name).length === 1,
      `actual format ${name} missing`,
    );
  const consumer = factory(204478),
    card = resolve(consumer, exportsOf(consumer, 204478).get("f")),
    timeBinding = binding(consumer, 529841);
  const invocation = exactlyOne(
    findNodes(
      card,
      (n) =>
        n.type === "CallExpression" &&
        n.arguments[0]?.type === "MemberExpression" &&
        member(n.arguments[0], timeBinding, "f"),
    ),
    "actual registered204478.f direct time consumer",
  );
  demand(
    objectProperty(invocation.arguments[1], "timestamp") &&
      objectProperty(invocation.arguments[1], "density"),
    "consumer props changed",
  );
  add(
    consumer,
    invocation,
    "actual204478.f card timestamp/density invocation (not its earlier shared-ID reply components)",
  );
  const formats = [];
  for (const f of factories.filter((f) => f.id === 890088)) {
    const exports = exportsOf(f, 890088),
      elapsed = resolve(f, exports.get("f"));
    const find = exactlyOne(
      findNodes(
        elapsed,
        (n) =>
          n.type === "CallExpression" &&
          n.callee.type === "MemberExpression" &&
          propertyName(n.callee.property) === "find",
      ),
      "elapsed units lookup",
    );
    const units = resolve(f, find.callee.object);
    demand(
      units?.type === "ArrayExpression",
      "elapsed units no longer literal",
    );
    formats.push({
      factory: f.provenance,
      elapsed: add(f, elapsed, "890088.f elapsed formatter"),
      units: add(f, units, "actual360day year/30day month unit table"),
      staticFormatter: add(
        f,
        resolve(f, exports.get("K")),
        "890088.K static corrected-clock relative label",
      ),
      title: add(
        f,
        resolve(f, exports.get("V")),
        "890088.V medium date/short time title",
      ),
    });
  }
  // Extract only actual Next Flight push string literals, then JSON data rows.
  const html = await corpus.capture("evidence/web/objects/d8e580782f84e190"),
    rows = [];
  demand(
    /<html\b[^>]*\blang="en"/.test(html.text),
    "English HTML language changed",
  );
  for (const script of html.text.matchAll(
    /<script\b[^>]*>([\s\S]*?)<\/script\s*>/gi,
  )) {
    let ast;
    try {
      ast = parse(script[1]);
    } catch {
      continue;
    }
    const scriptStart = script.index + script[0].indexOf(">") + 1;
    for (const push of findNodes(
      ast,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "MemberExpression" &&
        propertyName(n.callee.property) === "push" &&
        member(n.callee.object, "self", "__next_f"),
    )) {
      const tuple = push.arguments[0];
      if (
        tuple?.type !== "ArrayExpression" ||
        tuple.elements[0]?.value !== 1 ||
        tuple.elements[1]?.type !== "StringLiteral"
      )
        continue;
      const literal = tuple.elements[1];
      for (const line of literal.value.split("\n")) {
        if (!/^[0-9a-f]+:\{/.test(line)) continue;
        let data;
        try {
          data = JSON.parse(line.slice(line.indexOf(":") + 1));
        } catch {
          continue;
        }
        if (
          data?.locale === "en" &&
          data.resources?.time?.abbreviations &&
          data.resources?.common?.time_ago
        )
          rows.push({
            data,
            literal,
            scriptStart,
            rowId: line.slice(0, line.indexOf(":")),
          });
      }
    }
  }
  const english = exactlyOne(rows, "English locale/resources Flight row");
  const labels = english.data.resources.time.abbreviations;
  demand(
    JSON.stringify([
      labels.year,
      labels.month,
      labels.day,
      labels.hour,
      labels.minute,
      labels.second,
      english.data.resources.common.time_ago,
    ]) === JSON.stringify(["y", "mo", "d", "h", "m", "s", "{{time}} ago"]),
    "English relative labels changed",
  );
  const dictionary = html.witness(
    {
      start: english.scriptStart + english.literal.start,
      end: english.scriptStart + english.literal.end,
    },
    "inert actual Next Flight push literal containing locale=en resources; decoded as JSON data",
  );
  const implementation = [];
  for (const file of [
    "reconstruction/relative-time/model.mjs",
    "reconstruction/relative-time/model.d.mts",
    "packages/frontend/src/components/feed/RelativeTime.tsx",
    "packages/frontend/src/components/feed/FeedItem.tsx",
    "packages/frontend/src/components/feed/NativeCalloutFeed.tsx",
    "packages/frontend/src/app/api/server-time/route.ts",
  ])
    implementation.push({
      path: file,
      sha256: sha256(await fs.readFile(path.join(root, file))),
    });
  return {
    schemaVersion: 1,
    authority:
      "Authenticated inert AST and JSON data; no captured JavaScript execution",
    inputs: corpus.anchors,
    factories: factories.map((f) => ({ id: f.id, ...f.provenance })),
    entry: {
      id: 529841,
      export: "f",
      actualConsumer: {
        id: 204478,
        export: "f",
        invocation: consumer.witness(invocation, "direct component use"),
      },
    },
    formats,
    english: {
      locale: "en",
      units: {
        year: labels.year,
        month: labels.month,
        day: labels.day,
        hour: labels.hour,
        minute: labels.minute,
        second: labels.second,
      },
      suffix: english.data.resources.common.time_ago,
      rowId: english.rowId,
      originalLiteral: dictionary,
    },
    fragments,
    implementation,
    contract: {
      clockRead: {
        path: "/api/server-time",
        method: "GET (implicit fetch default)",
        cache: "no-store",
        credentials: "omit",
        timeoutMs: 5000,
        response: "successful JSON object with finite numeric nowMs",
        offset:
          "rounded serverNow minus client request/receive midpoint; absolute differences strictly below5000ms becomezero",
        successEligibilityMs: 900000,
        failureEligibilityMs: 60000,
        events:
          "first subscriber or becoming visible; ordinary display ticks do not sample",
      },
      tick: {
        serverSnapshot: 0,
        alignmentMs: 1000,
        visibility:
          "hidden stops display timer; visible refreshes snapshot/timer/sample",
        lastSubscriber:
          "unsubscribe outside notification cancels timer/removes visibility listener",
        quirk:
          "Original callback rearms unconditionally after emit, including synchronous last-unsubscribe inside emit; preserved",
      },
      parser:
        "nullish/invalid→null; Date→finite epochms; finite number<1e10 interpreted as seconds; other inputsDate.parse; no added Date-range guard",
      ui: "live defaults true; density comfortable; suffix defaults by density; title only after mount; ISOdateTime+suppressHydrationWarning; null timestamp uses supplied fallback",
      localReadImplementation:
        "Authored same-origin wall-clock GET response to the observed contract; original server internals/headers are unknown",
    },
    limits: [
      "English UI only; both captured890088 variants retained, no running variant selected",
      "Original custom-class/Tailwind merging is not exposed; no pixel-identity claim",
      "Existing notification668487.t injected-now attribution is a prerequisite; its files and behavior are unchanged",
      "No original backend internals/parity, authentication, ownership, social mutation, financial operation, route-ledger or compatibility-credit claim",
      "No other890088 numeric/locale-formatting exports reconstructed",
    ],
  };
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const mode = process.argv[2];
  demand(
    process.argv.length === 3 && ["--write", "--check"].includes(mode),
    "usage: --write|--check",
  );
  const text = JSON.stringify(await recoverRelativeTime(), null, 2) + "\n",
    destination = path.join(rootDefault, output);
  if (mode === "--write") await fs.writeFile(destination, text);
  else
    demand((await fs.readFile(destination, "utf8")) === text, "stale artifact");
  console.log(
    `${mode === "--write" ? "Wrote" : "Verified"} original relative time`,
  );
}
