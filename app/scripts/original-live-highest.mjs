import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  exactlyOne,
  findNodes,
  member,
  objectProperty,
  openCorpus,
  sha256,
} from "./original-contracts/source.mjs";

const appRoot = fileURLToPath(new URL("../", import.meta.url));
const contract = new URL(
  "../reconstruction/live-highest/contract.json",
  import.meta.url,
);

// Captured factories are parsed as AST data. No bundle or captured code runs.
export async function recoverHighestMarketCapSection() {
  const corpus = await openCorpus(appRoot);
  const homepage = await corpus.factory(31113, {
    source: "evidence/web/objects/8cb897425bbbb845.js",
  });
  const registry = await corpus.factory(944001, {
    source: "evidence/web/objects/0ba78d0f42544445.js",
  });
  const ids = await corpus.factory(788501, {
    source: "evidence/web/objects/44a65b4313e51497.js",
  });
  assert.equal(
    homepage.provenance.sha256,
    "aa72011769a3b4ed93846aa469860c5b661aafea0e98fbf5da8432305f2348c5",
  );
  assert.equal(
    registry.provenance.sha256,
    "1c56dd013720ae62a9c8ec316ebf1921d9fb13dc436bd75f7eefacdaad40aecb",
  );
  assert.equal(
    ids.provenance.sha256,
    "db885fc927427d144544ada8524614dc33547634693bc8824951e2a65c25f6f0",
  );

  function importBinding(factory, alias, id) {
    return exactlyOne(
      findNodes(
        factory.node,
        (node) =>
          node.type === "VariableDeclarator" &&
          node.id.type === "Identifier" &&
          node.id.name === alias &&
          node.init?.type === "CallExpression" &&
          member(node.init.callee, "e", "i") &&
          node.init.arguments[0]?.value === id,
      ),
      `${alias} import ${id}`,
    );
  }
  const registryImport = importBinding(homepage, "l", 944001);
  const rendererImport = importBinding(homepage, "n", 310766);
  const idsImport = importBinding(registry, "t", 788501);
  const registryExport = exactlyOne(
    findNodes(
      registry.node,
      (node) =>
        node.type === "CallExpression" &&
        member(node.callee, "e", "s") &&
        node.arguments[1]?.value === 944001,
    ),
    "registry export",
  );
  assert.equal(registry.text(registryExport.arguments[0]), '["Z",0,z,"A",0,P]');
  const wrapper = exactlyOne(
    findNodes(
      homepage.node,
      (node) =>
        node.type === "VariableDeclarator" &&
        node.id.name === "u" &&
        node.init?.type === "ArrowFunctionExpression",
    ),
    "used section wrapper",
  );
  const forwardedProps = exactlyOne(
    findNodes(
      wrapper,
      (node) =>
        node.type === "AssignmentExpression" &&
        node.left?.type === "ObjectPattern" &&
        node.right.name === "e",
    ),
    "wrapper props rest binding",
  );
  assert.equal(
    homepage.text(forwardedProps.left),
    "{isUnlocked:i,eager:l,...c}",
  );
  const forwardedRender = exactlyOne(
    findNodes(
      wrapper,
      (node) =>
        node.type === "CallExpression" &&
        node.arguments[0]?.type === "MemberExpression" &&
        member(node.arguments[0], "n", "Z"),
    ),
    "actual section renderer",
  );
  assert.equal(homepage.text(forwardedRender.arguments[1]), "{...c,eager:h}");
  const registryArray = exactlyOne(
    findNodes(
      registry.node,
      (node) =>
        node.type === "VariableDeclarator" &&
        node.id.name === "z" &&
        node.init?.type === "ArrayExpression",
    ),
    "section registry",
  ).init;
  assert.equal(registryArray.elements.length, 6);
  const entry = registryArray.elements[1];
  assert.equal(
    registry.text(objectProperty(entry, "id")),
    "t.f.HIGHEST_MARKET_CAP",
  );
  assert.equal(
    objectProperty(entry, "titleKey").value,
    "web.live.section_highest_market_cap",
  );
  assert.equal(
    registry.text(objectProperty(entry, "useFetch")),
    "e=>(0,i.N)({livePageSort:A.f.MARKET_CAP,...e})",
  );

  const sectionMap = exactlyOne(
    findNodes(
      homepage.node,
      (node) =>
        node.type === "CallExpression" &&
        node.callee?.type === "MemberExpression" &&
        node.callee.property.name === "map" &&
        member(node.callee.object, "l", "Z"),
    ),
    "registry map",
  );
  const callback = sectionMap.arguments[0];
  assert.deepEqual(
    callback.params.map((node) => node.name),
    ["e", "s"],
  );
  const render = callback.body;
  assert.equal(homepage.text(render.arguments[0]), "u");
  const props = render.arguments[1];
  assert.equal(homepage.text(objectProperty(props, "sectionId")), "e.id");
  assert.equal(homepage.text(objectProperty(props, "titleKey")), "e.titleKey");
  assert.equal(homepage.text(objectProperty(props, "initialData")), "v?.[s]");
  assert.equal(
    homepage.text(objectProperty(props, "onShowAll")),
    "()=>g.push(`/live/${e.id}`)",
  );
  const sourceProps = exactlyOne(
    findNodes(
      homepage.node,
      (node) =>
        node.type === "ObjectPattern" &&
        node.properties.some(
          (property) =>
            property.key?.name === "initialSectionData" &&
            property.value?.name === "v",
        ),
    ),
    "initialSectionData binding",
  );
  const sectionId = exactlyOne(
    findNodes(
      ids.node,
      (node) =>
        node.type === "AssignmentExpression" &&
        node.left?.type === "MemberExpression" &&
        !node.left.computed &&
        node.left.property.name === "HIGHEST_MARKET_CAP" &&
        node.left.object.type === "AssignmentExpression" &&
        node.left.object.left.name === "t" &&
        node.left.object.right.type === "ObjectExpression" &&
        node.right?.value === "highest-market-cap",
    ),
    "Highest market cap ID",
  );
  // The section renderer also produces the same Show-all destination directly.
  const rendererRoute = exactlyOne(
    findNodes(
      registry.node,
      (node) =>
        node.type === "TemplateLiteral" &&
        registry.text(node) === "`/live/${n}`",
    ),
    "Show-all href",
  );

  const capture = await corpus.capture("evidence/web/objects/c45d40b52df03727");
  assert.equal(
    capture.record.sha256,
    "aeff704c15d99482fe6e6347a92db0170dffeceb940a70e61dcc10002b006355",
  );
  const pushes = [
    ...capture.text.matchAll(
      /<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/gu,
    ),
  ];
  assert.equal(pushes.length, 1);
  const push = JSON.parse(pushes[0][1]);
  assert.equal(push[0], 1);
  const rows = push[1].split("\n");
  const resources = exactlyOne(
    rows.filter((row) => row.startsWith("7c:")),
    "captured translation resources",
  );
  const translatedLabel = JSON.parse(resources.slice(3)).resources.web.live
    .section_highest_market_cap;
  assert.equal(translatedLabel, "Highest market cap");
  assert.equal(
    rows.filter(
      (row) =>
        row.startsWith("116:I[31113,") && row.endsWith(',"LiveHomepage"]'),
    ).length,
    1,
  );
  const row = exactlyOne(
    rows.filter((row) => row.includes('"initialSectionData":')),
    "section Flight row",
  );
  const value = JSON.parse(row.slice(row.indexOf(":") + 1));
  assert.equal(value[1][1], "$L116");
  const sections = value[1][3].initialSectionData;
  assert.deepEqual(
    sections.map((items) => items.length),
    [42, 24],
  );
  const firstIds = new Set(sections[0].map((item) => item.id));
  const secondIds = sections[1].map((item) => item.id);
  assert.equal(new Set(secondIds).size, 24);
  assert.equal(secondIds.filter((id) => firstIds.has(id)).length, 24);

  return {
    schemaVersion: 1,
    section: {
      id: "highest-market-cap",
      index: 1,
      titleKey: "web.live.section_highest_market_cap",
      capturedEnglishLabel: translatedLabel,
      showAllPath: "/live/highest-market-cap",
    },
    anchors: corpus.anchors,
    factories: [homepage.provenance, registry.provenance, ids.provenance],
    witnesses: [
      homepage.witness(registryImport, "registry import"),
      homepage.witness(rendererImport, "section renderer import"),
      registry.witness(registryExport, "registry Z export"),
      homepage.witness(
        forwardedProps,
        "wrapper keeps initialData/label/id in rest props",
      ),
      homepage.witness(forwardedRender, "used renderer receives rest props"),
      registry.witness(idsImport, "ID enum import"),
      registry.witness(entry, "registry index 1"),
      homepage.witness(sourceProps, "Flight prop binding"),
      homepage.witness(
        sectionMap,
        "used section index, label and Show-all callback",
      ),
      ids.witness(sectionId, "literal section ID"),
      registry.witness(rendererRoute, "actual Show-all href"),
    ],
    flight: {
      source: capture.record.path,
      sha256: capture.record.sha256,
      bytes: capture.bytes.length,
      capturedAt: corpus.manifest.captured_at,
      homepageReference: "$L116",
      translatedLabelPath: "7c.resources.web.live.section_highest_market_cap",
      rowId: row.slice(0, row.indexOf(":")),
      firstCount: 42,
      secondCount: 24,
      intersectionCount: 24,
      orderedMints: secondIds,
      orderedMintSha256: sha256(Buffer.from(JSON.stringify(secondIds))),
    },
    limits: [
      "Captured membership/order and original label/route only; no ranking formula or current market-cap calculation.",
      "All 24 identities also occur in Most viewers; do not count them as additional unique streams.",
      "No original child-route HTML was captured. Native metadata disclosures and this page layout are local design.",
      "No captured JavaScript execution, live API, media playback, remote thumbnails, presence, wallet or coin-detail navigation.",
    ],
  };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const value = await recoverHighestMarketCapSection();
  const text = `${JSON.stringify(value, null, 2)}\n`;
  if (process.argv.includes("--write")) await writeFile(contract, text);
  else
    assert.equal(
      await readFile(contract, "utf8"),
      text,
      "Live section proof is stale",
    );
  console.log(
    "Verified captured Highest market cap registry/Flight/order/Show-all closure (24 records).",
  );
}
