import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
export const APP_ROOT = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/group-search-read-model";
const HASH = "9e5affafd605f47d6c9466659c4bc0a654fae027f4beff481337a1cdf1263828";
const own = (f, name) =>
  exactlyOne(
    f.node.body.body
      .flatMap((n) =>
        n.type === "VariableDeclaration"
          ? n.declarations
          : n.type === "FunctionDeclaration"
            ? [n]
            : [],
      )
      .filter((n) => n.id?.name === name),
    "source declaration " + name,
  );
const value = (f, name) => {
  const n = own(f, name);
  return n.type === "VariableDeclarator" ? n.init : n;
};
const ignored = new Set([
  "start",
  "end",
  "loc",
  "extra",
  "leadingComments",
  "trailingComments",
  "innerComments",
]);
const ast = (v) =>
  Array.isArray(v)
    ? v.map(ast)
    : v && typeof v === "object"
      ? Object.fromEntries(
          Object.entries(v)
            .filter(([k]) => !ignored.has(k))
            .map(([k, v]) => [k, ast(v)]),
        )
      : v;
const cite = (f, n, label) => ({ ...f.witness(n, label), text: f.text(n) });
// Bounded source-scope audit reused, credited from #1925. No shared parser edits.
function freeNames(node) {
  const result = new Set();
  const bind = (p, s) => {
    if (!p) return;
    if (p.type === "Identifier") s.add(p.name);
    else if (p.type === "ObjectPattern")
      p.properties.forEach((v) =>
        bind(v.type === "RestElement" ? v.argument : v.value, s),
      );
    else if (p.type === "ArrayPattern") p.elements.forEach((v) => bind(v, s));
    else if (p.type === "AssignmentPattern") bind(p.left, s);
    else if (p.type === "RestElement") bind(p.argument, s);
    else assert.fail("unreviewed binding " + p.type);
  };
  const walk = (n, sc = [], parent, key) => {
    if (!n || typeof n !== "object") return;
    if (Array.isArray(n)) {
      n.forEach((v) => walk(v, sc, parent, key));
      return;
    }
    let next = sc;
    if (
      [
        "FunctionDeclaration",
        "FunctionExpression",
        "ArrowFunctionExpression",
      ].includes(n.type)
    ) {
      const s = new Set();
      bind(n.id, s);
      n.params.forEach((p) => bind(p, s));
      next = [...sc, s];
    }
    if (n.type === "BlockStatement") {
      const s = new Set();
      for (const b of n.body) {
        if (b.type === "VariableDeclaration")
          b.declarations.forEach((d) => bind(d.id, s));
        if (b.type === "FunctionDeclaration") bind(b.id, s);
      }
      next = [...sc, s];
    }
    if (n.type === "CatchClause") {
      const s = new Set();
      bind(n.param, s);
      next = [...sc, s];
    }
    if (
      ["ForOfStatement", "ForInStatement"].includes(n.type) &&
      n.left.type === "VariableDeclaration"
    ) {
      const s = new Set();
      n.left.declarations.forEach((d) => bind(d.id, s));
      next = [...sc, s];
    }
    if (n.type === "Identifier") {
      const field =
        (["MemberExpression", "OptionalMemberExpression"].includes(
          parent?.type,
        ) &&
          key === "property" &&
          !parent.computed) ||
        (["ObjectProperty", "ObjectMethod"].includes(parent?.type) &&
          key === "key" &&
          !parent.computed) ||
        (["LabeledStatement", "BreakStatement", "ContinueStatement"].includes(
          parent?.type,
        ) &&
          key === "label");
      if (!field && !next.some((s) => s.has(n.name))) result.add(n.name);
      return;
    }
    for (const [k, v] of Object.entries(n))
      if (!ignored.has(k)) walk(v, next, n, k);
  };
  walk(node);
  return [...result].sort();
}

const contexts = [
  [
    "evidence/web/objects/c3601a995a6b7f37.js",
    "03c9e118088bd9ec60473d73d1cd014c8936d824c97c995f685fcedd6952007b",
    "8481cc43089c55a79f7d4c557e4bd7494c4b88ed78a42e6431fa74ae99e18071",
  ],
  [
    "evidence/web/objects/ecf7ec803bfb3020.js",
    "2f371de64d2eb89da7e8edd47f36faaf9b91b0d806a2b3800f03024e6783bd98",
    "159ae7ef2b2f7fc5357953d01c7c286b837c30539edfc1e9fd9b2043f81a230d",
  ],
  [
    "evidence/web/objects/9535b69d76e2a69b.js",
    "454ded6273c9cd1a419f8c2c0a726045df950fb56ee0ff522a48d098c3dbf307",
    "c80aeb14abca47a957356085d3c2b4005780d84567da801aa6f347ea2fedb937",
  ],
  [
    "evidence/web/objects/767cc801e3f88f8b.js",
    "95b5e23430f2f2fad80efa0fe423dcb89dcb9a5c5d0e5b0570df61882e3540ed",
    "a388f0a24b1eb774877703192ab5a21856928d916451cfe1b07bb46761d10268",
  ],
  [
    "evidence/web/objects/ea5d7a76f15713d7.js",
    "4d708b8f842a68b2a709a8c52ed67f33bda420281675aa079a646b16f2766f78",
    "3ddfd2396c08bd89dde3d3418eac9dbf536010a9ea3456983ab8f6310b62a8c6",
  ],
];
function exportsFor(f, id) {
  const map = new Map();
  for (const stmt of f.node.body.body) {
    const n = stmt.type === "ExpressionStatement" ? stmt.expression : null;
    if (n?.type !== "CallExpression" || !member(n.callee, f.runtime, "s"))
      continue;
    const target =
      n.arguments[1]?.value ??
      (f.provenance.ids.length === 1 ? f.provenance.ids[0] : null);
    if (target !== id) continue;
    const entries = n.arguments[0];
    assert.equal(entries.type, "ArrayExpression");
    assert.equal(entries.elements.length % 3, 0);
    for (let i = 0; i < entries.elements.length; i += 3) {
      const [name, kind, value] = entries.elements.slice(i, i + 3);
      assert.equal(name.type, "StringLiteral");
      assert.equal(kind.type, "NumericLiteral");
      assert.equal(kind.value, 0, "getter export must be reviewed separately");
      assert(!map.has(name.value));
      map.set(name.value, value);
    }
  }
  assert(map.size, "no actual export registration for " + id);
  return map;
}
function moduleClosure(f, id, names) {
  const exports = exportsFor(f, id),
    roots = names.map((name) => ({
      name,
      node: exactlyOne(
        [exports.get(name)].filter(Boolean),
        "actual export " + id + "." + name,
      ),
    }));
  const all = f.node.body.body.flatMap((n) =>
      n.type === "VariableDeclaration" ? n.declarations : [],
    ),
    declarations = new Map(all.map((n) => [n.id.name, n])),
    selected = new Set(),
    imports = new Map(),
    unknown = new Set();
  const visit = (node) => {
    for (const name of freeNames(node)) {
      if (selected.has(name) || imports.has(name)) continue;
      if (declarations.has(name)) {
        const d = declarations.get(name);
        if (
          d.init?.type === "CallExpression" &&
          ["i", "r"].some((method) => member(d.init.callee, f.runtime, method))
        ) {
          assert.equal(d.init.arguments[0].type, "NumericLiteral");
          imports.set(name, { id: d.init.arguments[0].value, node: d });
        } else {
          selected.add(name);
          visit(d.init);
        }
      } else unknown.add(name);
    }
  };
  roots.forEach((r) => visit(r.node));
  assert.deepEqual([...unknown].sort(), [], "unclosed source names " + id);
  const nodes = all.filter((n) => selected.has(n.id.name));
  return { roots, nodes, imports };
}
function declarations(f, nodes) {
  return nodes.map(
    (n) =>
      f.node.body.body.find(
        (s) => s.type === "VariableDeclaration" && s.declarations.includes(n),
      ).kind +
      " " +
      f.text(n) +
      ";",
  );
}
export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root),
    proofs = [],
    variants = [],
    frames = [],
    moduleCode = [];
  assert.equal(
    corpus.index.modules.filter((m) => m.ids.includes(560328)).length,
    5,
    "new reader variant requires review",
  );
  assert.equal(
    corpus.index.modules.filter((m) => m.ids.includes(760447)).length,
    5,
    "new schema variant requires review",
  );
  for (let i = 0; i < contexts.length; i++) {
    const [source, readerHash, schemaHash] = contexts[i],
      reader = await corpus.factory(560328, { source }),
      schema = await corpus.factory(760447, { source });
    assert.equal(reader.provenance.sha256, readerHash);
    assert.equal(schema.provenance.sha256, schemaHash);
    const rc = moduleClosure(reader, 560328, ["N", "B"]),
      sc = moduleClosure(schema, 760447, ["D", "Q", "A", "h", "t"]);
    assert.equal(rc.imports.size, 1);
    assert.equal([...rc.imports.values()][0].id, 760447);
    assert.deepEqual(
      [...sc.imports.values()].map((x) => x.id).sort((a, b) => a - b),
      [402030, 758045],
    );
    const imports = [...rc.imports]
      .map(([name, x]) => ({
        module: 560328,
        name,
        id: x.id,
        proof: cite(reader, x.node, "actual used reader import " + x.id),
      }))
      .concat(
        [...sc.imports].map(([name, x]) => ({
          module: 760447,
          name,
          id: x.id,
          proof: cite(schema, x.node, "actual used schema import " + x.id),
          variants: corpus.index.modules
            .filter((m) => m.ids.includes(x.id))
            .map((m) => ({ ids: m.ids, sha256: m.sha256, origins: m.origins })),
        })),
      );
    const localProofs = [
      ...rc.nodes.map((n) =>
        cite(reader, n, "complete reader declaration " + n.id.name),
      ),
      ...rc.roots.map((r) =>
        cite(reader, r.node, "actual reader export " + r.name),
      ),
      ...sc.nodes.map((n) =>
        cite(schema, n, "complete used schema declaration " + n.id.name),
      ),
      ...sc.roots.map((r) =>
        cite(schema, r.node, "actual schema/projection export " + r.name),
      ),
    ];
    proofs.push(...localProofs);
    variants.push({
      source,
      reader: reader.provenance,
      schema: schema.provenance,
      imports,
      readerLocals: rc.nodes.map((n) => n.id.name),
      schemaLocals: sc.nodes.map((n) => n.id.name),
      proofs: localProofs,
    });
    const schemaBindings = [...sc.imports].map(
      ([name, x]) =>
        "const " +
        name +
        "={" +
        (x.id === 402030 ? "contract:ports.contract" : "z:ports.z") +
        "};",
    );
    const readerBinding = "const " + [...rc.imports.keys()][0] + "=schema;";
    moduleCode.push(
      "function schema" + i + "(ports){",
      ...schemaBindings,
      ...declarations(schema, sc.nodes),
      "return {" +
        sc.roots
          .map((r) => JSON.stringify(r.name) + ":" + schema.text(r.node))
          .join(",") +
        "};",
      "}",
    );
    moduleCode.push(
      "function reader" + i + "(schema){",
      readerBinding,
      ...declarations(reader, rc.nodes),
      "return {" +
        rc.roots
          .map((r) => JSON.stringify(r.name) + ":" + reader.text(r.node))
          .join(",") +
        "};",
      "}",
    );
    frames.push({ i, reader, schema, rc, sc });
  }
  const code = [
    "// Complete ordinary shared-search group readers and used schema/projection constructors. Required API/runtime capabilities only.",
    ...moduleCode,
    "const contexts=" + JSON.stringify(contexts.map((x) => x[0])) + ";",
    "const schemas=[" +
      frames.map((x) => "schema" + x.i).join(",") +
      "],readers=[" +
      frames.map((x) => "reader" + x.i).join(",") +
      "];",
    "export function createGroupSearchReadModel(ports){",
    'if(!ports||typeof ports.z?.string!=="function"||!ports.contract?.["GET /groups/search"]?.response||!ports.contract?.["GET /users/{id}"]?.response)throw new TypeError("Explicit group schema runtime/contract responses required");',
    'const i=contexts.indexOf(ports.context);if(i<0)throw new TypeError("Explicit captured group source context required");',
    "const model=schemas[i](ports),request=readers[i](model);return{readGroup:request.N,searchGroups:request.B,projectSearchRow:model.h,projectProfile:model.t,groupRowSchema:model.D,profileSchema:model.Q,parseSearch:model.A};",
    "}",
  ].join("\n");
  const client = await prettier.format(code, { parser: "babel" }),
    emitted = parse(client, { sourceType: "module" });
  for (const { i, reader, schema, rc, sc } of frames) {
    for (const [type, f, c] of [
      ["reader", reader, rc],
      ["schema", schema, sc],
    ]) {
      const fn = exactlyOne(
          emitted.program.body.filter(
            (n) => n.type === "FunctionDeclaration" && n.id.name === type + i,
          ),
          "emitted " + type + i,
        ),
        ds = fn.body.body.flatMap((n) =>
          n.type === "VariableDeclaration" ? n.declarations : [],
        );
      for (const n of c.nodes)
        assert.deepEqual(
          ast(
            exactlyOne(
              ds.filter((d) => d.id.name === n.id.name),
              "emitted declaration " + n.id.name,
            ),
          ),
          ast(n),
          "complete used declaration changed",
        );
      const ret = exactlyOne(
        fn.body.body.filter((n) => n.type === "ReturnStatement"),
        "emitted export return",
      ).argument;
      for (const r of c.roots)
        assert.deepEqual(
          ast(
            exactlyOne(
              ret.properties.filter((p) => propertyName(p.key) === r.name),
              "emitted export " + r.name,
            ).value,
          ),
          ast(r.node),
          "complete exported value changed",
        );
    }
  }
  const main = await corpus.factory(238128, {
    source: "evidence/web/objects/ccb10fa3de5597c4.js",
  });
  assert.equal(main.provenance.sha256, HASH);
  const selectedCalls = findNodes(
    main.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      n.callee.expressions[1]?.type === "MemberExpression" &&
      ["eB"].includes(n.callee.expressions[1].object?.name) &&
      ["N", "B"].includes(propertyName(n.callee.expressions[1].property)),
  );
  assert.equal(selectedCalls.length, 2);
  proofs.push(
    ...selectedCalls.map((n) =>
      cite(main, n, "actual MAIN/RecentTerms group reader call"),
    ),
  );
  const schemaImport = own(main, "eo");
  assert.equal(schemaImport.init.arguments[0].value, 760447);
  proofs.push(
    cite(main, schemaImport, "actual shared row projection namespace"),
  );
  const projectCalls = findNodes(
    main.node,
    (n) =>
      n.type === "CallExpression" &&
      n.callee.type === "SequenceExpression" &&
      member(n.callee.expressions[1], "eo", "h"),
  );
  assert(projectCalls.length >= 1);
  proofs.push(
    ...projectCalls.map((n) =>
      cite(main, n, "actual MAIN/SearchRows group projection handoff"),
    ),
  );
  const contract = {
    schemaVersion: 1,
    scope:
      "Complete ordinary shared-search group profile/search readers, used schema constructors and projections; all physical contexts explicit, matching client/schema runtime capabilities supplied",
    clientSha256: sha256(client),
    manifestSha256: corpus.anchors.manifestSha256,
    contexts: variants,
    proofs,
    comparison:
      "Each emitted selected declaration/export value compares complete strict AST with its own physical source context; only parser positions/comments/raw spelling ignored. No alpha/type/operation/branch mask, capture execution or variant winner.",
    ports: {
      context:
        "Required exact captured object source path; no numeric-id winner/default",
      z: "Required existing schema runtime namespace with original string/nullish constructor API; runtime acquisition/equivalence unqualified",
      contract:
        "Required actual GET /groups/search and GET /users/{id} response-schema objects; captured shape/pick/extend/transform/parse operations retained. Schema/provider acquisition and original full runtime unknown, not reconstructed here",
      api: "Each reader requires source exact async function(operation,options) argument; client/origin/transport/auth/session acquisition/enforcement external. No credentials defaults added",
    },
    credits: {
      controller:
        "OPEN1925 actual MAINgroup query/pagination/key/abort lifecycle remains unchanged; this unit closes its required Breader and used parse/projection only",
      recent:
        "OPEN1962 group query/visibility lifecycle remains unchanged, Nreader path closed without copying parent frames",
      rows: "OPEN1937 actual760447.h row projection now supplied by this source model; row renderers unchanged/not copied; no hidden unmerged import",
      framework:
        "Existing shared physical-source authentication/free-binding proof reused unchanged; no graph identity/inventory or shared schema/parser modifications",
      responseSchema:
        "Existing API declaration/schema evidence credited. Required response/runtime ports preserve constructor semantics, not original schema runtime or full endpoint compatibility",
    },
    limits: [
      "Only560328.N/B and760447 used D/Q/A/h/t closure; grouped mutations/member/PnL/roles/account operations excluded/unexecuted",
      "No actual group/account/config/session/credential/cookie/storage acquisition, service request or client/auth/origin inference",
      "No query scheduler/keys/page/abort lifecycle is implemented; source input signal forwarded unchanged; query policy stays credited1925/1962port",
      "No backend/ranking/accounting/native/API/product/UI/visual/security/feature-completion or combinedruntime claim",
      "Finite supplied schemas/runtime and loopback API demonstrate bound constructor/parse/projection/read flow only; no original Zod error/whole response-schema/service fidelity inference",
    ],
  };
  return { client, contract: JSON.stringify(contract, null, 2) + "\n" };
}
export async function verify(root = APP_ROOT) {
  const g = await recover(root);
  for (const [file, text] of [
    ["client.mjs", g.client],
    ["contract.json", g.contract],
  ])
    assert.equal(
      await readFile(path.join(root, DIRECTORY, file), "utf8"),
      text,
      "canonical " + file + " changed",
    );
  return JSON.parse(g.contract);
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
)
  try {
    assert(
      process.argv.length === 3 &&
        ["--write", "--check"].includes(process.argv[2]),
      "usage: --write|--check",
    );
    if (process.argv[2] === "--write") {
      const g = await recover();
      await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
      for (const [file, text] of [
        ["client.mjs", g.client],
        ["contract.json", g.contract],
      ])
        await writeFile(path.join(APP_ROOT, DIRECTORY, file), text);
    } else await verify();
    console.log("PASS complete ordinary group search/read schema model");
  } catch (e) {
    console.error(e);
    process.exitCode = 1;
  }
