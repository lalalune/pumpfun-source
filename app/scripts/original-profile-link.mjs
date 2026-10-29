import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import prettier from "prettier";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  sha256,
} from "./original-contracts/source.mjs";
import { normalizeNavigation } from "./verify-search-navigation.mjs";

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIRECTORY = "reconstruction/profile-link";
const COMPONENT =
  "packages/frontend/src/components/leaderboard/original-profile-link.mjs";
const CLICK =
  "packages/frontend/src/components/leaderboard/original-profile-click.mjs";
const ROLES = {
  732486: { jsx: "jsx" },
  445242: { c: "useMemoCache" },
  146695: { $: "profileRoute" },
  458310: { default: "Link" },
  352386: { useContext: "useContext" },
  338319: { c: "classNames" },
  432405: { f: "isOrdinaryClick" },
};
const ast = (text) => parse(text, { sourceType: "module" });
const tail = (node) =>
  node.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function exported(factory, name) {
  const registration = exactlyOne(
    findNodes(
      factory.node,
      (n) =>
        n.type === "CallExpression" && member(n.callee, factory.runtime, "s"),
    ),
    "actual exports",
  );
  const values = registration.arguments[0].elements;
  const index = values.findIndex((n) => n?.value === name);
  assert.ok(index >= 0 && values[index + 1].value === 0);
  const value = values[index + 2];
  return value.type === "Identifier"
    ? exactlyOne(
        findNodes(
          factory.node,
          (n) => n.type === "FunctionDeclaration" && n.id?.name === value.name,
        ),
        "actual referenced function",
      )
    : value;
}
function imports(factory) {
  return findNodes(
    factory.node,
    (n) =>
      n.type === "VariableDeclarator" &&
      n.init?.type === "CallExpression" &&
      member(n.init.callee, factory.runtime, "i"),
  );
}
export async function buildProfileLink(appRoot = APP) {
  const corpus = await openCorpus(appRoot),
    outputs = new Map(),
    witnesses = [];
  const rows = corpus.index.modules.filter((row) => row.ids.includes(409954));
  assert.deepEqual(
    rows.map((row) => row.sha256).sort(),
    [
      "fcb2e40ca1d849a9432477c7265d3720b015d3ef3786aefde383cf1e0a3b62e9",
      "7c87904f8f332e95744b3d16ca40fce14e88a97bea5be93d5e44a835f5984c74",
    ].sort(),
  );
  let common, first, firstComponent, firstContext, firstImports;
  for (const row of rows) {
    const factory = await corpus.factory(409954, {
      source: row.origins[0].source,
    });
    const component = exported(factory, "o");
    const bindings = imports(factory),
      targets = {};
    assert.deepEqual(
      bindings.map((n) => n.init.arguments[0].value),
      Object.keys(ROLES)
        .map(Number)
        .sort((a, b) => {
          const order = [
            732486, 445242, 146695, 458310, 352386, 338319, 432405,
          ];
          return order.indexOf(a) - order.indexOf(b);
        }),
    );
    for (const imported of bindings)
      for (const [key, role] of Object.entries(
        ROLES[imported.init.arguments[0].value],
      ))
        targets[imported.id.name + "." + key] = "operation:" + role;
    const react = bindings.find((n) => n.init.arguments[0].value === 352386).id
      .name;
    const context = exactlyOne(
      findNodes(
        factory.node,
        (n) =>
          n.type === "VariableDeclarator" &&
          n.init?.type === "CallExpression" &&
          member(tail(n.init.callee), react, "createContext"),
      ),
      "actual null navigation context",
    );
    assert.deepEqual(
      context.init.arguments.map((n) => n.type),
      ["NullLiteral"],
    );
    const normalized = normalizeNavigation(
      component,
      { Symbol: "global:Symbol", [context.id.name]: "capability:context" },
      targets,
    );
    if (common)
      assert.deepEqual(
        normalized,
        common,
        "complete physical components differ beyond lexical bindings",
      );
    else {
      common = normalized;
      first = factory;
      firstComponent = component;
      firstContext = context;
      firstImports = bindings;
    }
    witnesses.push(
      factory.witness(
        component,
        "complete common ProfileLink component including inline context hook and compiler caches",
      ),
      factory.witness(context, "default null context, not authentication"),
    );
  }
  // This is a common implementation proven against BOTH whole components; it
  // does not select an unknown deployment/runtime winner.
  const aliases = firstImports
    .map(
      (n) =>
        `${n.id.name}={${Object.entries(ROLES[n.init.arguments[0].value])
          .map(([key, role]) => `${JSON.stringify(key)}:${role}`)
          .join(",")}}`,
    )
    .join(",");
  outputs.set(
    COMPONENT,
    await prettier.format(
      `"use client";\nexport {c as useMemoCache} from 'react/compiler-runtime';\nexport {profileRoute} from '../../../../../reconstruction/search-navigation/navigation.mjs';\n// Complete source-adapted common409954.o; original material retains its authorship.\n// Ports retain Next/React/class-merging/navigation boundaries; no bundle factory executes.\nexport function createProfileLinkModule({jsx,useMemoCache,useContext,createContext,Link,profileRoute,classNames,isOrdinaryClick}){const ${aliases};const ${firstContext.id.name}=createContext(null);const ProfileLink=${first.text(firstComponent)};return {ProfileLink,ProfileNavigationProvider:${firstContext.id.name}.Provider};}\n`,
      { parser: "babel" },
    ),
  );
  const ordinaryRows = corpus.index.modules.filter((row) =>
    row.ids.includes(432405),
  );
  assert.equal(ordinaryRows.length, 1);
  const ordinary = await corpus.factory(432405, {
    source: ordinaryRows[0].origins[0].source,
  });
  const guard = exported(ordinary, "f");
  outputs.set(
    CLICK,
    await prettier.format(
      `// Complete432405.f guard; no navigation or side effect is supplied.\nexport const isOrdinaryClick=${ordinary.text(guard)};\n`,
      { parser: "babel" },
    ),
  );
  witnesses.push(ordinary.witness(guard, "complete ordinary click guard"));
  const consumers = [];
  for (const row of corpus.index.modules.filter((row) =>
    row.ids.includes(996005),
  )) {
    const factory = await corpus.factory(996005, {
      source: row.origins[0].source,
    });
    const profile = exactlyOne(
      imports(factory).filter((n) => n.init.arguments[0].value === 409954),
      "actual trader link import",
    );
    const cover = exactlyOne(
      findNodes(
        factory.node,
        (n) =>
          n.type === "CallExpression" &&
          member(
            tail(n.callee),
            imports(factory).find((n) => n.init.arguments[0].value === 732486)
              .id.name,
            "jsx",
          ) &&
          member(n.arguments[0], profile.id.name, "o") &&
          n.arguments[1]?.type === "ObjectExpression" &&
          n.arguments[1].properties.some(
            (p) => p.key?.value === "data-row-cover",
          ),
      ),
      "actual trader-row profile link cover",
    );
    const id = exactlyOne(
      cover.arguments[1].properties.filter((p) => p.key?.name === "profileId"),
      "actual supplied profileId",
    ).value;
    assert.equal(id.type, "MemberExpression");
    assert.equal(id.property.name, "walletAddress");
    witnesses.push(
      factory.witness(
        profile,
        "actual trader row imports complete ProfileLink",
      ),
      factory.witness(cover, "actual trader row links supplied wallet address"),
    );
    consumers.push(factory.provenance);
  }
  const selector = exactlyOne(
    corpus.index.modules.filter((row) => row.ids.includes(146695)),
    "shared profile route module",
  );
  const route = await corpus.factory(146695, {
    source: selector.origins[0].source,
  });
  witnesses.push(
    route.witness(
      exported(route, "$"),
      "profileRoute already recovered by accepted search navigation; reused without new recovery credit",
    ),
  );
  const maintained = ast(outputs.get(COMPONENT));
  const adapted = exactlyOne(
    findNodes(
      maintained,
      (n) => n.type === "VariableDeclarator" && n.id.name === "ProfileLink",
    ),
    "used adapted component",
  ).init;
  const targets = {};
  for (const imported of firstImports)
    for (const [key, role] of Object.entries(
      ROLES[imported.init.arguments[0].value],
    ))
      targets[imported.id.name + "." + key] = "operation:" + role;
  assert.deepEqual(
    normalizeNavigation(
      adapted,
      { Symbol: "global:Symbol", [firstContext.id.name]: "capability:context" },
      targets,
    ),
    common,
  );
  const contract = {
    schema: 1,
    source: {
      manifestSha256: corpus.anchors.manifestSha256,
      selectedEntries: corpus.index.modules.filter((row) =>
        row.ids.some((id) => [409954, 432405, 146695, 996005].includes(id)),
      ),
    },
    commonCompleteComponentAstSha256: sha256(JSON.stringify(common)),
    consumers,
    witnesses,
    outputs: Object.fromEntries(
      [...outputs].map(([name, text]) => [name, sha256(text)]),
    ),
    boundaries: [
      "Original null-default navigation context and pending UI state are not backend authentication or ownership.",
      "React/compiler runtime, Next Link and class merging remain explicit ports. Original private navigation provider is not implemented.",
      "URL builder is reused from accepted search-navigation; no additional recovery count.",
      "The full two physical component ASTs agree; no arbitrary deployment winner is selected.",
    ],
  };
  return { outputs, contract };
}
export async function verifyProfileLink(appRoot = APP) {
  const result = await buildProfileLink(appRoot);
  for (const [name, text] of result.outputs)
    assert.equal(
      await readFile(path.join(appRoot, name), "utf8"),
      text,
      "adapted common component changed: " + name,
    );
  assert.equal(
    await readFile(path.join(appRoot, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(result.contract, null, 2) + "\n",
  );
  return result.contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv[2] === "--write") {
    const result = await buildProfileLink();
    await mkdir(path.join(APP, DIRECTORY), { recursive: true });
    for (const [name, text] of result.outputs) {
      await mkdir(path.dirname(path.join(APP, name)), { recursive: true });
      await writeFile(path.join(APP, name), text);
    }
    await writeFile(
      path.join(APP, DIRECTORY, "contract.json"),
      JSON.stringify(result.contract, null, 2) + "\n",
    );
  } else {
    assert.equal(process.argv[2], "--check");
    await verifyProfileLink();
  }
  console.log(
    "Verified both complete ProfileLink components, common AST, real trader callers and ordinary-click guard; provider/class/runtime boundaries remain explicit",
  );
}
