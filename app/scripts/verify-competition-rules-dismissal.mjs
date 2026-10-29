import assert from "node:assert/strict";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  sha256,
} from "./original-contracts/source.mjs";
import { normalizeNavigation } from "./verify-search-navigation.mjs";
const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DIR = "reconstruction/competition-rules-dismissal";
const tail = (n) =>
  n.type === "SequenceExpression" ? n.expressions.at(-1) : n;
const funcs = new Set([
  "FunctionDeclaration",
  "FunctionExpression",
  "ArrowFunctionExpression",
]);
function imported(f, id) {
  return exactlyOne(
    findNodes(
      f.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        member(n.init.callee, f.runtime, "i") &&
        n.init.arguments[0]?.value === id,
    ),
    "actual import " + id,
  );
}
function exported(f, id, key) {
  const call = exactlyOne(
      findNodes(
        f.node,
        (n) =>
          n.type === "CallExpression" &&
          member(n.callee, f.runtime, "s") &&
          n.arguments[1]?.value === id,
      ),
      "actual module exports " + id,
    ),
    values = call.arguments[0].elements;
  for (let i = 0; i < values.length; ) {
    const name = values[i].value;
    const direct =
      values[i + 1].type === "NumericLiteral" && values[i + 1].value === 0;
    if (name === key) return values[i + (direct ? 2 : 1)];
    i += direct ? 3 : 2;
  }
  throw Error("missing actual export " + id + "." + key);
}
const booleanDefault = (f, key, value) =>
  exactlyOne(
    findNodes(
      f,
      (n) =>
        n.type === "ObjectProperty" &&
        n.key?.name === key &&
        n.value?.type === "AssignmentPattern" &&
        n.value.right.type === "UnaryExpression" &&
        n.value.right.operator === "!" &&
        n.value.right.argument.value === (value ? 0 : 1),
    ),
    "actual default " + key,
  );
export async function rulesDismissalEvidence(app = APP) {
  const c = await openCorpus(app),
    witnesses = [];
  const required = new Map([
    [
      590407,
      "3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda",
    ],
    [
      439587,
      "556a5e98fc389f458883751f5ed829f9493c87444c6f5053b676b34a39f05fa9",
    ],
    [
      524684,
      "4a95dd69ab776beb22fce660c865256c7cc7ddc091c08d949c92213f537a1f1d",
    ],
    [
      566023,
      "d037edfec9edb41cb70bd60e126b7315ebfaec3e9e7caff00dbb301bbdeb2dd4",
    ],
    [
      385676,
      "d18763456faf1ae85d0d574aba879b0fe2f8515be76364d8d9687c11ff60ec6d",
    ],
  ]);
  const factories = new Map();
  for (const [id, hash] of required) {
    const rows = c.index.modules.filter((r) => r.ids.includes(id));
    assert.deepEqual(
      rows.map((r) => r.sha256),
      [hash],
      "reviewed physical context set changed",
    );
    factories.set(
      id,
      await c.factory(id, { source: rows[0].origins[0].source }),
    );
  }
  const rules = factories.get(590407),
    marker = exactlyOne(
      findNodes(
        rules.node,
        (n) => n.type === "StringLiteral" && n.value === "cup-rules-dialog",
      ),
      "actual Rules dialog marker",
    );
  const wrapper = findNodes(
    rules.node,
    (n) => funcs.has(n.type) && n.start < marker.start && n.end > marker.end,
  ).sort((a, b) => a.end - a.start - (b.end - b.start))[0];
  const modalImport = imported(rules, 439587),
    targets = {};
  for (const [id, roles] of [
    [732486, { jsx: "jsx" }],
    [445242, { c: "memo" }],
    [398902, { f: "translation" }],
    [439587, { v: "modalRoot", s: "modalContent" }],
  ])
    for (const [key, role] of Object.entries(roles))
      targets[imported(rules, id).id.name + "." + key] = "operation:" + role;
  const content = exactlyOne(
    findNodes(
      wrapper,
      (n) =>
        n.type === "CallExpression" &&
        n.arguments[0]?.type === "Identifier" &&
        n.arguments[1]?.type === "ObjectExpression" &&
        n.arguments[1].properties.some((p) => p.key?.name === "competition"),
    ),
    "actual Rules body capability",
  );
  const normalized = normalizeNavigation(
    wrapper,
    {
      Symbol: "global:Symbol",
      [content.arguments[0].name]: "capability:content",
    },
    targets,
  );
  assert.equal(
    sha256(JSON.stringify(normalized)),
    "c38f55e1f033262de49e78d01b358e8f9a11dcdfb772c299c57a5dc89eb407f1",
  );
  const rootCall = exactlyOne(
    findNodes(
      wrapper,
      (n) =>
        n.type === "CallExpression" &&
        member(n.arguments[0], modalImport.id.name, "v"),
    ),
    "actual Rules modal root call",
  );
  assert.deepEqual(
    rootCall.arguments[1].properties.map((p) => p.key.name),
    ["isOpen", "onIsOpenChange", "children"],
  );
  witnesses.push(
    rules.witness(
      wrapper,
      "complete actual Rules modal controller: state/callback forwarding with no pointer-dismissal override",
    ),
    rules.witness(modalImport, "Rules imports439587 responsive dialog"),
  );
  const ui = factories.get(439587),
    v = exported(ui, 439587, "v"),
    s = exported(ui, 439587, "s");
  const names = exactlyOne(
    findNodes(
      ui.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, ui.runtime, "S") &&
        n.arguments[1]?.value === 396623,
    ),
    "actual named re-export registration",
  );
  const entries = names.arguments[0].elements,
    i = entries.findIndex((n) => n?.value === "Root,DrawerRoot");
  assert.ok(i > 0);
  assert.equal(entries[i - 1].name, imported(ui, 524684).id.name);
  assert.ok(
    findNodes(
      v,
      (n) =>
        n.type === "ObjectProperty" &&
        n.key?.name === "swipeDirection" &&
        n.value.value === "down",
    ).length === 1,
  );
  assert.ok(
    !findNodes(
      v,
      (n) =>
        n.type === "ObjectProperty" &&
        n.key?.name === "disablePointerDismissal",
    ).length,
  );
  witnesses.push(
    ui.witness(
      v,
      "complete used dialog root wrapper; caller props forwarded, no dismissal override",
    ),
    ui.witness(s, "complete used portal/backdrop/viewport/popup composition"),
    ui.witness(
      names,
      "existing1717 graph boundary reused: actual396623.Root maps to524684.DrawerRoot",
    ),
  );
  const root = factories.get(524684),
    drawer = exported(root, 524684, "DrawerRoot"),
    inner = exported(root, 660315, "Root");
  for (const [node, label] of [
    [drawer, "used DrawerRoot"],
    [inner, "actual underlying dialog Root"],
  ]) {
    witnesses.push(
      root.witness(
        booleanDefault(node, "disablePointerDismissal", false),
        label + " defaults pointer dismissal enabled",
      ),
      root.witness(
        booleanDefault(node, "modal", true),
        label + " defaults modal true",
      ),
    );
  }
  const forwarded = exactlyOne(
    findNodes(
      drawer,
      (n) =>
        n.type === "ObjectProperty" &&
        n.key?.name === "disablePointerDismissal" &&
        n.value.type === "Identifier",
    ),
    "forwarded pointer-dismissal capability",
  );
  assert.equal(
    forwarded.value.name,
    booleanDefault(drawer, "disablePointerDismissal", false).value.left.name,
  );
  const outside = exactlyOne(
    findNodes(
      root.node,
      (n) => n.type === "ObjectMethod" && n.key?.name === "outsidePress",
    ),
    "actual used outside press predicate",
  );
  witnesses.push(
    root.witness(
      forwarded,
      "DrawerRoot forwards the actual default to dialogRoot",
    ),
    root.witness(
      outside,
      "actual non-left/multitouch/nesting/backdrop eligibility predicate",
    ),
  );
  const policy = exactlyOne(
    findNodes(
      root.node,
      (n) => n.type === "ObjectProperty" && n.key?.name === "outsidePressEvent",
    ),
    "used outside press event policy",
  );
  assert.ok(root.text(policy).includes('"intentional"'));
  witnesses.push(
    root.witness(
      policy,
      "registered backdrop selects intentional press policy",
    ),
  );
  const backdrop = factories.get(566023);
  witnesses.push(
    backdrop.witness(
      backdrop.node,
      "actual DrawerBackdrop attaches store backdropRef; original bytes only",
    ),
  );
  const dismiss = factories.get(385676),
    intentional = exactlyOne(
      findNodes(
        dismiss.node,
        (n) =>
          n.type === "ObjectProperty" &&
          n.key?.name === "intentional" &&
          n.value.value === "onClick",
      ),
      "intentional means click",
    );
  const handler = exactlyOne(
    findNodes(
      dismiss.node,
      (n) =>
        n.type === "FunctionDeclaration" &&
        findNodes(
          n,
          (m) =>
            m.type === "CallExpression" &&
            member(m.callee, "y", "setOpen") &&
            m.arguments[0]?.type === "UnaryExpression",
        ).length > 0 &&
        dismiss.text(n).includes("outsidePress"),
    ),
    "actual outside press dismissal handler",
  );
  const release = exactlyOne(
    findNodes(
      dismiss.node,
      (n) =>
        n.type === "FunctionDeclaration" &&
        dismiss.text(n).includes('"pointercancel"===e.type'),
    ),
    "actual release/cancel suppression",
  );
  witnesses.push(
    dismiss.witness(
      intentional,
      "intentional outside press uses click, not initial pointerdown",
    ),
    dismiss.witness(handler, "actual eligible outside press sets open false"),
    dismiss.witness(
      release,
      "actual inside-start release/cancel click suppression",
    ),
  );
  return {
    schema: 1,
    source: {
      manifestSha256: c.anchors.manifestSha256,
      selectedEntries: c.index.modules.filter((r) =>
        r.ids.some((id) => required.has(id)),
      ),
    },
    wrapperAstSha256: sha256(JSON.stringify(normalized)),
    witnesses,
    attribution: [
      "Reuse accepted source-reader and lexical comparator; no captured factory evaluated.",
      "Credit1717 named re-export/optional registration graph diagnostics and1665 Search caller-native light-dismiss evidence; neither generic unit is copied or altered.",
    ],
    limits: [
      "Current retained source contexts are explicit; no deployment/runtime winner is inferred.",
      "Native closedby-any is a bounded local browser mapping of outside dismissal, not a full Drawer/FloatingUI/provider/swipe/nested behavior reconstruction.",
    ],
  };
}
export async function verifyRulesDismissal(app = APP) {
  const expected =
    JSON.stringify(await rulesDismissalEvidence(app), null, 2) + "\n";
  assert.equal(
    await readFile(path.join(app, DIR, "contract.json"), "utf8"),
    expected,
  );
  const source = await readFile(
      path.join(
        app,
        "packages/frontend/src/app/leaderboard/competition-rules.tsx",
      ),
      "utf8",
    ),
    tree = parse(source, {
      sourceType: "module",
      plugins: ["typescript", "jsx"],
    });
  const dialog = exactlyOne(
    findNodes(
      tree,
      (n) => n.type === "JSXOpeningElement" && n.name?.name === "dialog",
    ),
    "actual native Rules dialog",
  );
  assert.equal(
    exactlyOne(
      dialog.attributes.filter(
        (n) => n.type === "JSXAttribute" && n.name.name === "closedby",
      ),
      "actual light-dismiss admission",
    ).value.value,
    "any",
  );
  return JSON.parse(expected);
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  if (process.argv[2] === "--write") {
    await mkdir(path.join(APP, DIR), { recursive: true });
    await writeFile(
      path.join(APP, DIR, "contract.json"),
      JSON.stringify(await rulesDismissalEvidence(), null, 2) + "\n",
    );
  } else {
    assert.equal(process.argv[2], "--check");
    await verifyRulesDismissal();
  }
  console.log(
    "Rules caller/default/actual outside-press source chain authenticated; native browser mapping remains bounded",
  );
}
