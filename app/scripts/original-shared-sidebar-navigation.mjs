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
export const DIRECTORY = "reconstruction/shared-sidebar-navigation";
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
    specs = [
      [
        103547,
        "13c13db9eb86191b.js",
        "a3f92e0aa42472b121190dc3f0cbaeaf495ad1d80b8d3aaf06835779db394434",
      ],
      [
        721426,
        "13c13db9eb86191b.js",
        "84f074bca773d01c2507e778b3855c4d4ff9a64c55c6e48dcac82417eb4e960a",
      ],
      [
        309166,
        "13c13db9eb86191b.js",
        "26506ac655f6d37023cb246f3a18519cc674551f9473642cd7ee2672a4a96bfe",
      ],
      [
        4327,
        "b677d332af92b7f5.js",
        "920ca733bc3858c5c8bf09749f76c456839d7f790e393b97d2d77dc97d5f693a",
      ],
      [
        532160,
        "13c13db9eb86191b.js",
        "92d6895266c587d79443d98ed9b4c1880ee3b3a3bdff83296ee592ad284a9486",
      ],
    ],
    indexEntries = [],
    factories = [];
  for (const [id, file, hash] of specs) {
    const entries = corpus.index.modules.filter((r) => r.ids.includes(id));
    assert.equal(entries.length, 1);
    assert.equal(entries[0].origins.length, 1);
    assert.equal(entries[0].sha256, hash);
    indexEntries.push(entries[0]);
    factories.push(
      await corpus.factory(id, { source: "evidence/web/objects/" + file }),
    );
  }
  const [family, nav, controller, marker, matcher] = factories,
    retained = [];
  const copy = (f, node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const exportNames = [
    "Sidebar",
    "SidebarContent",
    "SidebarFooter",
    "SidebarHeader",
    "SidebarInset",
    "SidebarMenu",
    "SidebarMenuButton",
    "SidebarMenuItem",
    "SidebarProvider",
    "SidebarRail",
    "SidebarTrigger",
    "useSidebar",
  ];
  const bindings = new Map(
    exportNames.map((name) => [name, exported(family, 103547, name).name]),
  );
  assert.deepEqual(
    [...bindings.values()],
    ["C", "I", "A", "E", "k", "T", "O", "R", "j", "S", "N", "_"],
  );
  const declarations = [
    "v",
    "w",
    "j",
    "C",
    "N",
    "S",
    "k",
    "E",
    "A",
    "I",
    "T",
    "R",
    "L",
    "O",
  ].map((name) =>
    copy(
      family,
      declaration(family, name),
      "complete original Sidebar dependency/public declaration " + name,
    ),
  );
  const functions = ["c", "_", "M", "D"].map((name) =>
    copy(
      family,
      fn(family, name),
      "complete used original Sidebar function " + name,
    ),
  );
  const displayNames = [
    "j",
    "C",
    "N",
    "S",
    "k",
    "E",
    "A",
    "I",
    "T",
    "R",
    "O",
  ].map((name) =>
    copy(
      family,
      exactlyOne(
        findNodes(
          family.node,
          (n) =>
            n.type === "AssignmentExpression" &&
            member(n.left, name, "displayName"),
        ),
        name + " original displayName",
      ),
      "original public component displayName " + name,
    ),
  );
  assert.equal(
    findNodes(
      family.node,
      (n) => n.type === "MemberExpression" && n.property.name === "cookie",
    ).length,
    0,
    "actual provider has no cookie access",
  );
  const groupFunctions = [
    "ea",
    "ei",
    "en",
    "es",
    "eo",
    "ec",
    "ed",
    "eu",
    "eB",
  ].map((name) =>
    copy(
      nav,
      fn(nav, name),
      "complete ordinary supplied-item group/action renderer " + name,
    ),
  );
  const rowClass = copy(
      nav,
      declaration(nav, "el"),
      "complete original action-list local frame class",
    ),
    controllerFn = copy(
      controller,
      exported(controller, 309166, "SidebarController"),
      "complete actual SidebarController defaultOpen/root marker handoff",
    ),
    rootMarker = copy(
      marker,
      declaration(marker, "l"),
      "actual shared data-app-shell marker only; consent core external",
    ),
    pathMatch = copy(
      matcher,
      exported(matcher, 532160, "f"),
      "actual contextual532160 path-boundary matcher, not119524 icon",
    );
  const activeNode = exactlyOne(
    findNodes(
      exported(nav, 721426, "AppSidebar"),
      (n) =>
        n.type === "ArrowFunctionExpression" &&
        n.params.length === 4 &&
        findNodes(
          n,
          (n) =>
            n.type === "ObjectProperty" && n.key.name === "watchlistRowShown",
        ).length > 0,
    ),
    "complete original primary route-active policy",
  );
  const active = copy(
      nav,
      activeNode,
      "complete original route-active policy; supplied route mapping/session-row visibility only",
    ),
    explore = copy(
      nav,
      declaration(nav, "ew"),
      "actual Explore route constant",
    ),
    watchlist = copy(
      nav,
      declaration(nav, "ev"),
      "actual watchlist query value constant",
    );
  const text = await prettier.format(
    `// Complete source-adapted shared Sidebar controller/display and ordinary supplied navigation rendering. No acquisition/actions implemented.
export function createSharedSidebarNavigation({jsx,jsxs,Fragment,React,useMemoCache,classNames,classVariants,Slot,TooltipRoot,TooltipTrigger,TooltipContent,DrawerRoot,DrawerContent,DrawerHeader,DrawerTitle,DrawerDescription,makeSvgIcon,useTranslation,window,Link,NewBadge,ExternalIcon,routes}){
 const sidebar=(()=>{const t={jsx,jsxs,Fragment},r={c:useMemoCache},l=React,y={c:classNames},n={f:classVariants},i={M:Slot},a={W:TooltipRoot,_:TooltipTrigger,Y:TooltipContent},x={j:DrawerRoot,U:DrawerContent,D:DrawerHeader,L:DrawerTitle,c:DrawerDescription},s={f:useTranslation},o={f:makeSvgIcon};${functions.join("\n")}let ${declarations.join(",")};${displayNames.map((t) => t + ";").join("\n")}return {${[...bindings].map(([name, id]) => name + ":" + id).join(",")}};})();
 const t={jsx,jsxs,Fragment},r={c:useMemoCache},er={c:classNames},et=sidebar,c={default:Link},v={f:NewBadge},i={x8:ExternalIcon},u={Fragment};let ${rowClass};${groupFunctions.join("\n")}
 const SidebarController=(()=>{const t={jsx},r={c:useMemoCache},i=sidebar;let ${rootMarker};const a={p:l};return ${controllerFn};})();
 const pathMatches=${pathMatch};const isNavigationActive=(()=>{const ex={f:pathMatches},e_=routes;let ${explore},${watchlist};return ${active};})();
 return {...sidebar,SidebarController,NavGroup:ea,ActionList:es,Group:eB,pathMatches,isNavigationActive};}`,
    { parser: "babel" },
  );
  const wrapper = exactlyOne(
      findNodes(
        parse(text, { sourceType: "module" }),
        (n) =>
          n.type === "FunctionDeclaration" &&
          n.id?.name === "createSharedSidebarNavigation",
      ),
      "actualusedconstructor",
    ),
    counts = new Map();
  for (const n of findNodes(wrapper, () => true)) {
    const hash = astHash(n);
    counts.set(hash, (counts.get(hash) ?? 0) + 1);
  }
  for (const r of retained)
    assert.equal(
      counts.get(r.astSha256),
      1,
      "complete original region exactlyonce in usedwrapper:" + r.label,
    );
  const html = await corpus.capture("evidence/web/objects/b713215f09b03c14");
  assert.equal(
    html.record.sha256,
    "5c54a668997394767a338ff5efe132ba3400bd5e1c4b6bb16c9c075b6a389409",
  );
  const chunks = [],
    citations = [];
  for (const m of html.text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)) {
    if (!m[1].includes("self.__next_f.push")) continue;
    const base = m.index + m[0].indexOf(">") + 1;
    const ast = parse(m[1], { sourceType: "script" });
    for (const call of findNodes(
      ast,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "MemberExpression" &&
        n.callee.property.name === "push" &&
        n.callee.object.type === "MemberExpression" &&
        n.callee.object.object.name === "self" &&
        n.callee.object.property.name === "__next_f",
    )) {
      const a = call.arguments[0];
      if (
        a?.type === "ArrayExpression" &&
        a.elements[0]?.value === 1 &&
        a.elements[1]?.type === "StringLiteral"
      ) {
        chunks.push(a.elements[1].value);
        if (/SidebarController|AppSidebar|10a:|10b:/.test(a.elements[1].value))
          citations.push(
            html.witness(
              {
                start: base + a.elements[1].start,
                end: base + a.elements[1].end,
              },
              "actual parsed rawHTML Flight StringLiteral data, neverexecuted",
            ),
          );
      }
    }
  }
  assert.equal(chunks.length, 3);
  const flight = chunks.join("").split("\n"),
    record = (id) =>
      exactlyOne(
        flight.filter((l) => l.startsWith(id + ":")),
        id + " actualserializedrecord",
      ).slice(id.length + 1),
    imports = ["10d", "10e", "10f"].map((id) => ({
      id,
      value: JSON.parse(record(id).slice(1)),
    }));
  assert.equal(record("10d")[0], "I");
  assert.equal(record("10e")[0], "I");
  assert.equal(record("10f")[0], "I");
  assert.equal(imports[0].value[0], 309166);
  assert.equal(imports[1].value[0], 721426);
  assert.equal(imports[2].value[0], 103547);
  assert.equal(JSON.parse(record("10c")), "SidebarController");
  assert.equal(imports[0].value[2], "$10c");
  assert.equal(imports[1].value[2], "AppSidebar");
  assert.equal(imports[2].value[2], "SidebarInset");
  const layout = ["10a", "10b"].map((id) => {
    const node = JSON.parse(record(id));
    assert.equal(node[1], "$L10d");
    assert.equal(node[3].defaultOpen, false);
    assert.equal(node[3].children[0][1], "$L10e");
    assert.equal(node[3].children[1][1], "$L10f");
    return {
      id,
      type: node[1],
      defaultOpen: node[3].defaultOpen,
      children: node[3].children.map((n) => n[1]),
    };
  });
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete12export original sharedSidebar family+actualController+ordinary supplieditem navigation/action display+route-active policy; upperAppSidebar/provider/actions excluded",
    indexEntries,
    factories: factories.map((f) => f.provenance),
    retained,
    publicSidebarExports: Object.fromEntries(bindings),
    witnesses: [
      nav.witness(
        exported(nav, 721426, "AppSidebar"),
        "actual upperAppSidebar consumer only; provider/action/app-promotion initialization NOTimplemented",
      ),
      nav.witness(imported(nav, 103547), "actual Sidebar family import"),
      controller.witness(
        imported(controller, 103547),
        "actual controller family import",
      ),
      controller.witness(
        imported(controller, 4327),
        "actual shared rootmarker import; consent external",
      ),
      nav.witness(
        declaration(nav, "e_"),
        "actual route metadata mapping only; routes supplied, excluded targets not exposed",
      ),
      nav.witness(
        imported(nav, 532160),
        "actual contextual pathmatcher import",
      ),
      family.witness(
        imported(family, 206261),
        "actual mobile Drawer namespace; primitiveport",
      ),
      family.witness(
        imported(family, 439587),
        "actual Tooltip namespace; primitiveport",
      ),
    ],
    capturedRoot: {
      source: "evidence/web/objects/b713215f09b03c14",
      sha256: html.record.sha256,
      bytes: html.record.bytes,
      citations,
      imports: imports.map((r) => ({
        record: r.id,
        module: r.value[0],
        export: r.value[2],
      })),
      controllerExportString: JSON.parse(record("10c")),
      layout,
      limit:
        "Static observed anonymous capturedlayout admission only, no original server/RSC/runtime/auth/visitor-state implementation orparity",
    },
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    credit:
      "685capturedshell integration/529markup+CSS and1398/1434/1483/1429native lifecycle/1556HeaderBack remain unchanged.4327 consent marker/532160 matcher usedonly asactual dependencies, no copiedconsent/wholefactory/vendor claim. No nativepage orpriorquery/sourcepacket edits.",
    limits: [
      "Whole103547provider hasNOcookie/storage. Preserve controlled/uncontrolled desktopstate, independent mobilefunctionalstate, toggle-time native767px mediaquery, lowercaseb+Meta/Ctrl keydown/listenercleanup and capturedstate functionalupdater quirks.",
      "Sidebar always returns desktop+mobile structures withoriginalCSSvisibility. Drawer/Tooltip/Slot/CVA/Link/SVG/icon ports external; no native focus-trap, animation, browserRouter/vendor/CSS/pixel parity.",
      "Only suppliedsafe navigation items/route mapping/activeflags and inert syntheticcallbacks. ActualAppSidebar flags/address/session/chat/account/actions andexcluded support/Terminal/nativeapp/deferredcontrols NOTimplemented/acquired/exposed.",
      "DefaultOpenfalse is observed in2actualcapturedrootlayoutnodes; provider absentdefault remains originaltrue. Not an inferred globalserver policy oruser preference.",
      "No actualcookies/storage/session/credentials/user/account/preferences/flags/provider acquisition/live requests/trading/admin/backend/security/completionclaim.",
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
    "Verified full original shared Sidebar/navigation/controller family; safe supplied items and explicit primitive/action ports",
  );
}
