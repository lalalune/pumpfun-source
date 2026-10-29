import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  objectProperty,
  propertyName,
  literal,
} from "./original-contracts/source.mjs";
const ROOT = fileURLToPath(new URL("..", import.meta.url));
export const OUTPUT = "reconstruction/create-banner/contract.json";
const EXPECTED = [
  [
    734638,
    "89ce7de3b9bad421",
    "616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc",
  ],
  [
    586090,
    "6a1606765ef3e83e",
    "5ddcdce058dfb79522bc03a2ba9bf7d9cae7eccccaad65d80ea43b368f114fc4",
  ],
  [
    66094,
    "6a1606765ef3e83e",
    "a47ef1abe034e30194f5ebc662e2dddefb6beb96a7a9d9cd04f639d6cf664f2d",
  ],
  [
    29542,
    "fd402d4185b44ce9",
    "ede316c07dd8ceb3faff4f840fefbb61a5b1a18d372e600225db0f8410a661bd",
  ],
  [
    658259,
    "762f0784b7be61c0",
    "691ff5f669927ccece0478631066f80ac94a832dd5fadae2a3a175f09372e6fa",
  ],
  [
    320853,
    "01f240a1f9100e9d",
    "f11b9e82b5951d62d9717dad92358a120241bab0e6453ad8550cd8f2775975d9",
  ],
];
export async function recover(root = ROOT) {
  const corpus = await openCorpus(root),
    factories = [];
  for (const [id, chunk, hash] of EXPECTED) {
    const f = await corpus.factory(id, {
      source: `evidence/web/objects/${chunk}.js`,
    });
    assert.equal(f.provenance.sha256, hash, `changed selected factory ${id}`);
    factories.push(f);
  }
  const [page, constants, resize, labels, selector, loader] = factories;
  const html = await corpus.capture("evidence/web/objects/5e15667ed36cac85");
  assert.equal(html.record.url, "https://pump.fun/create");
  assert.ok(html.text.includes(new URL(page.provenance.url).pathname));
  assert.ok(html.text.includes(new URL(constants.provenance.url).pathname));
  // These are the exact selected siblings in retained Create HTML, not global-ID guesses.
  const top = (name) =>
    exactlyOne(
      page.node.body.body
        .flatMap((n) => n.declarations ?? [])
        .filter((n) => n.id?.name === name),
      `top ${name}`,
    );
  const lazy = top("$"),
    wrapper = top("K");
  assert.ok(page.text(lazy).includes("e.A(320853)"));
  assert.ok(page.text(wrapper).includes("{...e}"));
  assert.ok(loader.text().includes("m(658259)"));
  assert.equal(
    new URL(selector.provenance.url).pathname.split("/").at(-1),
    "3r6p9e97ury3w.js",
  );
  assert.ok(loader.text().includes("static/immutable/chunks/3r6p9e97ury3w.js"));
  const nativeInput = exactlyOne(
    findNodes(
      selector.node,
      (n) => n.type === "CallExpression" && n.arguments[0]?.value === "input",
    ),
    "native selector input",
  );
  assert.equal(selector.text(nativeInput), '(0,t.jsx)("input",{...a()})');
  const banner = exactlyOne(
    findNodes(
      page.node,
      (n) =>
        n.type === "CallExpression" &&
        n.arguments[0]?.name === "K" &&
        n.arguments[1]?.type === "ObjectExpression" &&
        n.arguments[1].properties.some(
          (p) => propertyName(p.key) === "isBanner",
        ),
    ),
    "separate banner consumer",
  );
  const props = banner.arguments[1];
  assert.equal(literal(objectProperty(props, "isBanner")), true);
  assert.equal(literal(objectProperty(props, "maxFiles")), 1);
  assert.equal(page.text(objectProperty(props, "accept")), "eX.G");
  assert.equal(page.text(objectProperty(props, "onDrop")), "e=>ta(e)");
  const bindings = (name, contains) =>
    exactlyOne(
      findNodes(
        page.node,
        (n) =>
          n.type === "VariableDeclarator" &&
          n.id?.name === name &&
          page.text(n).includes(contains),
      ),
      `actual ${name} binding`,
    );
  const choose = bindings("ta", "e7(r)");
  assert.ok(page.text(choose).includes("a.ok?ep(a.file):tr(a.reason)"));
  const normalize = bindings("e7", "resized");
  assert.ok(
    page.text(normalize).includes('"image/gif"===r||await (0,eJ.q)(e)'),
  );
  assert.ok(page.text(normalize).includes("e.size>1e6||Math.max(a,i)>3e3"));
  const sniff = bindings("e9", "eX.G");
  const upload = bindings("e6", "pin-banner");
  assert.ok(page.text(upload).includes("ti({mint:t.toBase58(),fileUri:r})"));
  const attach = bindings("ti", "POST /coins/add-banner");
  const freeCreate = bindings("te", "POST /coins/create-v2");
  assert.ok(
    page
      .text(freeCreate)
      .includes(
        'if(!("mint"in a)||!a.mint)throw Error("could not create coin");let{mint:i}=a;await e6(new l.PublicKey(i))',
      ),
  );
  const confirmedAttach = exactlyOne(
    findNodes(
      page.node,
      (n) =>
        n.type === "CallExpression" &&
        n.arguments[0]?.type === "ObjectExpression" &&
        n.arguments[0].properties.some(
          (p) => propertyName(p.key) === "attachBanner",
        ),
    ),
    "confirmation-bound banner attach",
  );
  assert.equal(
    page.text(objectProperty(confirmedAttach.arguments[0], "attachBanner")),
    "()=>e6(S)",
  );
  const bound = bindings("e5", "eX.O.BANNER");
  const exports = exactlyOne(
    findNodes(
      constants.node,
      (n) =>
        n.type === "CallExpression" &&
        n.callee?.object?.name === constants.runtime &&
        propertyName(n.callee.property) === "s",
    ),
    "constants export",
  ).arguments[0].elements;
  const exportValue = (name) =>
    exports[exports.findIndex((n) => n?.value === name) + 2];
  const accepted = exactlyOne(
    constants.node.body.body
      .flatMap((n) => n.declarations ?? [])
      .filter((n) => n.id?.name === exportValue("G").name),
    "banner accept map",
  ).init.properties.map((p) => propertyName(p.key));
  assert.deepEqual(accepted, [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
  ]);
  assert.equal(literal(objectProperty(exportValue("O"), "BANNER")), 4500000);
  const guidance = exactlyOne(
    findNodes(
      labels.node,
      (n) =>
        n.type === "ObjectProperty" &&
        propertyName(n.key) === "BANNER" &&
        n.value.type === "ObjectExpression" &&
        n.value.properties.some((p) => propertyName(p.key) === "DESCRIPTION"),
    ),
    "banner guidance",
  );
  assert.ok(labels.text(guidance).includes("recommended"));
  const previewClass = exactlyOne(
    findNodes(
      selector.node,
      (n) => n.type === "StringLiteral" && n.value.includes("aspect-[3/1]"),
    ),
    "banner preview frame",
  );
  const witness = (f, n, label) => ({
    ...f.witness(n, label),
    code: f.text(n),
  });
  return {
    authority:
      "Static authenticated captured frontend evidence; original JavaScript is never executed.",
    anchors: corpus.anchors,
    createHtml: {
      path: html.record.path,
      sha256: html.record.sha256,
      bytes: html.record.bytes,
      selectedPageAndCommonChunkPresent: true,
    },
    factories: factories.map((f) => f.provenance),
    observed: {
      accepted,
      maximumBytes: 4500000,
      maximumFiles: 1,
      bannerIsSeparateFromCoinImage: true,
      recommendation: "3:1,1500x500; not a hard dimension gate",
      productionAttach:
        "Separate pin/upload then POST /coins/add-banner after creation; not token metadata.",
    },
    witnesses: [
      witness(page, lazy, "lazy selector loader edge"),
      witness(page, wrapper, "K forwards selector props"),
      witness(loader, loader.node, "actual lazy selector chunk/factory"),
      witness(selector, nativeInput, "native selector input"),
      witness(page, banner, "actual optional banner consumer"),
      witness(page, choose, "used selection/normalization result"),
      witness(page, bound, "banner limit source"),
      witness(
        page,
        normalize,
        "production normalization NOT implemented locally",
      ),
      witness(page, sniff, "production MIME sniff NOT implemented locally"),
      witness(page, upload, "separate production pin/attach boundary EXCLUDED"),
      witness(page, attach, "separate production request EXCLUDED"),
      witness(
        page,
        freeCreate,
        "banner attach after successful create response EXCLUDED",
      ),
      witness(
        page,
        confirmedAttach,
        "banner attach awaits actual confirmation EXCLUDED",
      ),
      witness(
        labels,
        guidance,
        "recommendation and historical production wording",
      ),
      witness(selector, previewClass, "banner display frame"),
    ],
    localAdaptation: {
      anonymousEphemeralPicker: true,
      mimeDeclaredOnly: true,
      inputBytes: 4500000,
      maximumDecodedPixels: 16777216,
      timeoutMs: 10000,
      normalizationImplemented: false,
      tokenMetadataChanged: false,
      noUploadUriOrChainOperation: true,
    },
    limits: [
      "No source equivalence for normalization, MIME sniffing, authentication or upload.",
      "Historical irreversibility wording does not apply to a reversible offline draft.",
      "Pixel frame is display-only; file bytes are unchanged.",
    ],
  };
}
const direct =
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (direct) {
  const result = `${JSON.stringify(await recover(), null, 2)}\n`,
    out = path.join(ROOT, OUTPUT);
  if (process.argv.includes("--check"))
    assert.equal(await readFile(out, "utf8"), result);
  else {
    await mkdir(path.dirname(out), { recursive: true });
    await writeFile(out, result);
  }
  console.log("create banner captured contract: PASS");
}
