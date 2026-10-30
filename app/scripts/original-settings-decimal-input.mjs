// Captures are authenticated/parsed as data; no captured factory is evaluated.
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
  objectProperty,
  sha256,
} from "./original-contracts/source.mjs";

export const APP = fileURLToPath(new URL("..", import.meta.url));
export const DIRECTORY = "reconstruction/settings-decimal-input";
const target = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function exported(factory, id, name) {
  const found = [];
  for (const node of findNodes(
    factory.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, factory.runtime, "s"),
  )) {
    if (
      node.arguments[1]
        ? node.arguments[1].value !== id
        : factory.ids.length !== 1 || factory.id !== id
    )
      continue;
    const values = node.arguments[0].elements;
    for (let index = 0; index < values.length; index += 3)
      if (values[index].value === name) found.push(values[index + 2]);
  }
  return exactlyOne(found, `${id}.${name} actual export`);
}
const declaration = (factory, name) =>
  exactlyOne(
    factory.node.body.body
      .filter((node) => node.type === "VariableDeclaration")
      .flatMap((node) => node.declarations)
      .filter((node) => node.id.name === name),
    `${name} module declaration`,
  );
const imported = (factory, id) =>
  exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "VariableDeclarator" &&
        node.init?.type === "CallExpression" &&
        member(node.init.callee, factory.runtime, "i") &&
        node.init.arguments[0]?.value === id,
    ),
    `${id} import`,
  );
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .filter(
        ([key]) =>
          ![
            "start",
            "end",
            "loc",
            "extra",
            "comments",
            "leadingComments",
            "trailingComments",
            "innerComments",
          ].includes(key),
      )
      .map(([key, child]) => [key, canonical(child)]),
  );
}
const astHash = (node) => sha256(Buffer.from(JSON.stringify(canonical(node))));

const fn = (factory, name) =>
  exactlyOne(
    factory.node.body.body.filter(
      (node) => node.type === "FunctionDeclaration" && node.id.name === name,
    ),
    name + " complete function",
  );
export async function recover(root = APP) {
  const corpus = await openCorpus(root),
    entries = corpus.index.modules.filter((r) => r.ids.includes(124884));
  assert.equal(entries.length, 1);
  assert.equal(entries[0].origins.length, 1);
  assert.equal(
    entries[0].sha256,
    "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
  );
  const f = await corpus.factory(124884, {
      source: "evidence/web/objects/4490d02ba2117672.js",
    }),
    retained = [];
  const copy = (node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const frame = copy(
      declaration(f, "C"),
      "complete original local numeric-input frame class; shared choice styling already1872",
    ),
    regex = copy(
      declaration(f, "ea"),
      "complete original decimal draft grammar",
    ),
    input = copy(
      fn(f, "eo"),
      "complete original decimal draft input renderer/state/handlers",
    );
  const text = await prettier.format(
    `// Complete original decimal draft input; supplied numeric props/callback only.
export function createSettingsDecimalInput({jsx,jsxs,useMemoCache,useState}){const t={jsx,jsxs},i={c:useMemoCache},n={useState};let ${frame};let ${regex};${input}return eo;}`,
    { parser: "babel" },
  );
  const wrapper = exactlyOne(
    findNodes(
      parse(text, { sourceType: "module" }),
      (n) =>
        n.type === "FunctionDeclaration" &&
        n.id?.name === "createSettingsDecimalInput",
    ),
    "used exported constructor",
  );
  for (const r of retained)
    assert.equal(
      findNodes(wrapper, (n) => astHash(n) === r.astSha256).length,
      1,
      "full original region exactly once in used wrapper",
    );
  const dispatcher = fn(f, "ed"),
    branch = exactlyOne(
      findNodes(
        dispatcher,
        (n) =>
          n.type === "IfStatement" &&
          n.test.type === "BinaryExpression" &&
          n.test.left.value === "number" &&
          member(n.test.right, "g", "kind"),
      ),
      "actual number branch",
    ),
    caller = exactlyOne(
      findNodes(
        branch,
        (n) =>
          n.type === "CallExpression" &&
          member(target(n.callee), "t", "jsx") &&
          n.arguments[0]?.name === "eo",
      ),
      "actual numeric renderer call",
    );
  assert.deepEqual(
    caller.arguments[1].properties.map((p) => p.key.name),
    ["value", "onCommit", "min", "step", "unit", "label", "isDisabled"],
  );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete used original Settings decimal-draft React input renderer with synthetic supplied props/callback, not numeric preference acquisition",
    indexEntry: entries[0],
    factory: f.provenance,
    retained,
    witnesses: [
      f.witness(
        branch,
        "actual1872 number-kind dispatcher conversion/callback/props/Row consumer; dispatcher external",
      ),
      f.witness(caller, "exact original supplied numeric props boundary"),
      f.witness(
        imported(f, 547562),
        "actual dispatcher setting-value/setter framework import;1839external, no preference read",
      ),
      f.witness(
        imported(f, 196796),
        "actual dispatcher mounted-state gate import; external, no hydration/provider claim",
      ),
    ],
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    credit:
      "1872 already retains the full ed dispatcher with NumberInput port;1839 state and1920 Row remain external. This recovers the missing complete eo renderer, not another dispatcher/framework. C styling shared with1872 is exact local dependency, not a newly claimed helper.",
    limits: [
      "Only supplied value/onCommit/min/step/unit/label/isDisabled. No descriptor acquisition/storage/provider/account/trading/admin values or preferences mutation. Callback is a synthetic commit port, not original persistence.",
      "Source allows numeric draft characters with comma→dot, at most12 UTF-16 code units; empty/dot/zero remain draft without commit. Positive finite raw Number commits immediately and optional Math.max min applies without new min validation/max/rounding/step enforcement.",
      "Focus snapshots String(value); active draft masks parent controlled changes; blur drops draft and exposes latest controlled value. Callback errors propagate after draft state enqueue, no new rollback. Native disabled prevents interaction; handler itself adds no disabled guard.",
      "Step is forwarded on type=text, not an implemented increment/validation policy. Original classes retained; diagnostic CSS does not establish original pixels/full UI/provider/native/security/completion parity.",
    ],
  };
  return { text, contract };
}
export async function verify(root = APP) {
  const r = await recover(root);
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "client.mjs"), "utf8"),
    r.text,
  );
  assert.equal(
    await readFile(path.join(root, DIRECTORY, "contract.json"), "utf8"),
    JSON.stringify(r.contract, null, 2) + "\n",
  );
  return r.contract;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv.includes("--write")) {
    const r = await recover();
    await mkdir(path.join(APP, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP, DIRECTORY, "client.mjs"), r.text);
    await writeFile(
      path.join(APP, DIRECTORY, "contract.json"),
      JSON.stringify(r.contract, null, 2) + "\n",
    );
  } else await verify();
  console.log(
    "Verified full original Settings decimal draft input and actual dispatcher consumer; synthetic callback boundary preserved",
  );
}
