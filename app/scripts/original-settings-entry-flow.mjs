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
export const DIRECTORY = "reconstruction/settings-entry-flow";
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
  const corpus = await openCorpus(root);
  const specs = [
      [
        443032,
        "13c13db9eb86191b.js",
        "9460ff6fdae4376cb7f2d8eac055c346a27df8102701dba683b0705b43c2af03",
      ],
      [
        487832,
        "f1d0a5f42b599cd2.js",
        "e26c1fcfb77bb0d91146bc4a948d43b33b5ef842cf4f9d10ef62ea240d4d6cd3",
      ],
      [
        532757,
        "994c0030bcc62017.js",
        "034384d1b986c91f5f6c6d019267c14a8f950c51b29f88fe0ede276277bb94df",
      ],
      [
        298590,
        "e02656dccdb8d127.js",
        "57913ac77552c8014bc1e073d52b68311f22d05a57005562baa86325b86f738d",
      ],
      [
        190147,
        "4490d02ba2117672.js",
        "82201da29940aa3f9a95fa6daa47335f0d58ab8f4926ceaecf490a410df8560e",
      ],
      [
        124884,
        "4490d02ba2117672.js",
        "dfcb487f79e63fa817cef92fd322e172c6d44fb2270bad175820a463b2e382ea",
      ],
    ],
    factories = [],
    indexEntries = [];
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
  const [host, opener, catalog, loader, bridge, modal] = factories,
    retained = [];
  const copy = (f, node, label) => {
    retained.push({
      label,
      source: f.witness(node, label),
      astSha256: astHash(node),
    });
    return f.text(node);
  };
  const event = copy(
      opener,
      declaration(opener, "t"),
      "complete original module event-name declaration",
    ),
    open = copy(
      opener,
      exported(opener, 487832, "v"),
      "complete original URL-before-event opener; truthy settingId",
    ),
    schema = copy(
      host,
      declaration(host, "c"),
      "complete actual enum/string multi-query schema declaration",
    ),
    lazy = copy(
      host,
      declaration(host, "u"),
      "complete dynamic modal declaration/load callback/SSR metadata",
    ),
    component = copy(
      host,
      exported(host, 443032, "SettingsModalHost"),
      "complete original Host including atomic multi-query controller/effect/conditional mount",
    );
  const text = await prettier.format(
    `// Source-adapted original Settings URL/event/controller/mount owner. Capabilities are explicit.
export function createSettingsEntryFlow({window,URL,CustomEvent,jsx,useMemoCache,useEffect,useFeatureFlag,settingsFlag,parseAsStringEnum,parseAsString,useQueryStates,sectionIds,dynamic,loadModule}){
 const event=(()=>{let ${event};return {eventName:t,openSettings:${open}}})();
 const t={jsx},r={c:useMemoCache},a={D:{WEB_SETTINGS_HUB:settingsFlag}},i={k:useFeatureFlag},n={default:dynamic},l={useEffect},s={b:parseAsStringEnum,d:parseAsString,i:useQueryStates},o={m:sectionIds},d={O:event.eventName},e={A:loadModule};
 let ${schema};let ${lazy};const SettingsModalHost=${component};return {...event,SettingsModalHost};}`,
    { parser: "babel" },
  );
  const wrapper = exactlyOne(
    findNodes(
      parse(text, { sourceType: "module" }),
      (n) =>
        n.type === "FunctionDeclaration" &&
        n.id?.name === "createSettingsEntryFlow",
    ),
    "actual used constructor",
  );
  for (const region of retained)
    assert.equal(
      findNodes(wrapper, (n) => astHash(n) === region.astSha256).length,
      1,
      "complete source region exactly once in actual used constructor",
    );
  // Check static namespace chain, without loading any captured code or chunks.
  assert.equal(
    findNodes(
      loader.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee.type === "Identifier" &&
        n.callee.name === "t" &&
        n.arguments[0]?.value === 190147,
    ).length,
    1,
  );
  assert.equal(
    findNodes(
      bridge.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, "e", "i") &&
        n.arguments[0]?.value === 124884,
    ).length,
    1,
  );
  const modalExport = exported(modal, 124884, "SettingsModal");
  assert.equal(modalExport.type, "FunctionExpression");
  const catalogIds = declaration(catalog, "t").init.elements.map(
    (n) => objectProperty(n, "id").value,
  );
  const contract = {
    schema: 1,
    reviewBase: "094a06f18df738d41e77070c1a009e135671ac1a",
    scope:
      "Complete original Settings URL/event opener and host/controller/conditional dynamic-mount flow, with explicit schema/multi-query, feature flag and modal capabilities",
    indexEntries,
    factories: factories.map((f) => f.provenance),
    retained,
    witnesses: [
      host.witness(
        imported(host, 311282),
        "actual single atomic multi-query/schema import; vendor implementation external",
      ),
      host.witness(
        imported(host, 532757),
        "actual section enum metadata import",
      ),
      host.witness(
        imported(host, 487832),
        "actual event-name import joining opener to host",
      ),
      host.witness(
        imported(host, 322315),
        "actual WEB_SETTINGS_HUB flag-key source",
      ),
      host.witness(
        imported(host, 254010),
        "actual feature availability hook; provider external",
      ),
      host.witness(
        imported(host, 453706),
        "actual dynamic renderer import; runtime external",
      ),
      catalog.witness(
        declaration(catalog, "t"),
        "actual section metadata; labels/catalog already675/683, not copied",
      ),
      catalog.witness(
        exported(catalog, 532757, "m"),
        "actual exported section ID projection",
      ),
      loader.witness(
        loader.node,
        "actual static chunk loader to190147; not executed",
      ),
      bridge.witness(
        bridge.node,
        "actual190147 namespace bridge to124884; not executed",
      ),
      modal.witness(
        modalExport,
        "actual SettingsModal export target; child implementation external",
      ),
    ],
    queryLibraryIndex: corpus.index.modules.filter((r) =>
      r.ids.includes(311282),
    ),
    catalogIds,
    module: {
      path: DIRECTORY + "/client.mjs",
      sha256: sha256(Buffer.from(text)),
    },
    capabilities: {
      query:
        "Required parseAsStringEnum(sectionIds),parseAsString and atomic useQueryStates(schema,{history:replace,clearOnDefault:true}). No replacement by two single-key hooks, vendor parser/scheduling/cache/SSR parity or whole311282 recovery.",
      browser:
        "Supplied window,URL,CustomEvent for helper and host listener. Synthetic owned URL/history/event state only in tests; no cookies/storage/session/account acquisition.",
      feature:
        "Required useFeatureFlag(settingsFlag) bound to original WEB_SETTINGS_HUB selection; no feature-provider or permission acquisition.",
      modal:
        "Required dynamic(loadCallback,{loadableGenerated:{modules:[190147]},ssr:false}) and loadModule(298590)→Promise<{SettingsModal}>. Static captured chain is bound but neither capture loaders nor protected child providers executed/reconstructed.",
    },
    credit:
      "675/683 catalog/context,868 accepted single-query subset (not atomic multiquery API),1911resource,1920focus,1898results,1952content,1872dispatcher and1839state remain credited external capabilities. No unmerged imports/copies or helper retally.",
    limits: [
      "Helper uses truthy settingId; host callback uses nullish conversion and close clears both keys. URL writes precede event dispatch even without host listener; no new rollback/error/cancellation behavior.",
      "Host flag/listener cleanup and null branch conditional child unmount are preserved. Dynamic runtime/cache/loading/SSR/provider behavior remains capability-supplied, not native/global Settings integration.",
      "Only synthetic fresh browser URL/history/event and readonly modal probe; no actualcookies/storage/sessions/credentials/user/account/preference/protected/trading/admin data, acquisition or mutations. No originalNuqs/Next/native/API/pixel/fullapp/security/completion claim.",
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
    "Verified full original Settings URL/event/controller/mount owner; query/dynamic/provider ports preserved",
  );
}
