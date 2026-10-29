import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  exactlyOne,
  findNodes,
  openCorpus,
  sha256,
} from "./original-contracts/source.mjs";

const root = fileURLToPath(new URL("../", import.meta.url));
const contract = new URL(
  "../reconstruction/live-hero/contract.json",
  import.meta.url,
);

export async function recoverLiveHero() {
  const corpus = await openCorpus(root);
  const source = "evidence/web/objects/44a65b4313e51497.js";
  const selections = [
    [
      31113,
      "evidence/web/objects/8cb897425bbbb845.js",
      "aa72011769a3b4ed93846aa469860c5b661aafea0e98fbf5da8432305f2348c5",
    ],
    [
      133244,
      source,
      "248fcf72a5bbbd3cb39cd391e161c90c6d496a0828ec3e07c15e7df093aecd97",
    ],
    [
      859960,
      source,
      "d97c7c9447e248dcaeef4b872bb869c9056d2979cdf53731913116fb8544e429",
    ],
    [
      369731,
      source,
      "fc87a2c85f17569e3f50a0b0bd960e814109550629c9baef4200792008e6d9b3",
    ],
    [
      218921,
      source,
      "7741ad9f49b1ac1f9aacd299cb09413750cde77f2db613d2a539489938126782",
    ],
  ];
  const factories = [];
  for (const [id, source, hash] of selections) {
    const factory = await corpus.factory(id, { source });
    assert.equal(factory.provenance.sha256, hash);
    factories.push(factory);
  }
  const [homepage, loader, query, carousel, dots] = factories;
  const witnesses = [];
  function used(factory, type, text, label) {
    const node = exactlyOne(
      findNodes(
        factory.node,
        (node) => node.type === type && factory.text(node) === text,
      ),
      label,
    );
    witnesses.push(factory.witness(node, label));
    return node;
  }
  used(
    homepage,
    "VariableDeclarator",
    "c=e.i(133244)",
    "actual hero loader import",
  );
  used(
    homepage,
    "ObjectProperty",
    "initialHeroData:x",
    "actual initialHeroData binding",
  );
  used(
    homepage,
    "CallExpression",
    "(0,t.jsx)(c._,{initialData:x})",
    "initialHeroData reaches hero loader",
  );
  used(loader, "VariableDeclarator", "i=e.i(369731)", "actual carousel import");
  used(loader, "VariableDeclarator", "c=e.i(859960)", "actual query import");
  used(loader, "VariableDeclarator", "o=6", "six original hero slots");
  used(
    loader,
    "CallExpression",
    'e.s(["E",()=>o,"_",()=>m,"g",()=>d])',
    "actual loader and mint-based DTO mapper exports",
  );
  used(
    loader,
    "ObjectPattern",
    "{initialData:f}",
    "loader initialData parameter binding",
  );
  used(loader, "CallExpression", "(0,c.L)(d)", "hero query consumed by loader");
  used(
    loader,
    "ObjectExpression",
    "{initialData:f}",
    "loader forwards initial data",
  );
  used(
    loader,
    "CallExpression",
    "(0,t.jsx)(i.HeroCarousel,{livestreams:h})",
    "actual query data reaches carousel",
  );
  used(
    query,
    "CallExpression",
    'e.s(["A",()=>j,"t",()=>_,"L",()=>N,"N",()=>E],859960)',
    "L exports the used hero query",
  );
  used(
    query,
    "ObjectExpression",
    "{queryKey:t,queryFn:i,initialData:n,staleTime:o}",
    "hero query retains captured initialData",
  );
  used(
    query,
    "CallExpression",
    "(0,l.useQuery)(r)",
    "actual hero query options consumed",
  );
  used(
    carousel,
    "ObjectExpression",
    "{itemCount:S.length,isLooping:!0}",
    "used count and looping policy",
  );
  used(
    carousel,
    "CallExpression",
    "(0,r.useState)(0)",
    "initial selected index zero",
  );
  used(
    carousel,
    "ObjectExpression",
    "{selectedIndex:f,nextIndex:p,previousIndex:v,hasPrevious:g,hasNext:b,setSelectedIndex:h}",
    "actual selection hook result",
  );
  used(
    carousel,
    "ArrowFunctionExpression",
    "()=>{u?h(e=>(e+1)%d):x(1)}",
    "used looping next transition",
  );
  used(
    carousel,
    "ArrowFunctionExpression",
    "()=>{u?h(e=>(e-1+d)%d):x(-1)}",
    "used looping previous transition",
  );
  used(
    carousel,
    "ArrowFunctionExpression",
    "e=>{F.current=!1,U(e)}",
    "direct selection callback",
  );
  used(
    carousel,
    "VariableDeclarator",
    "i=P===a",
    "selected slot derives from actual selected index",
  );
  used(
    carousel,
    "ObjectProperty",
    '"data-selected":i',
    "actual selected slot attribute",
  );
  used(
    carousel,
    "CallExpression",
    "(0,t.jsx)(u.PaginationDots,{count:S.length,selectedIndex:P,onSelect:V})",
    "actual dot consumer",
  );
  used(
    carousel,
    "ObjectProperty",
    "onClickCapture:e=>{a!==P&&(e.preventDefault(),e.stopPropagation(),V(a))}",
    "nonselected slot selects before excluded navigation",
  );
  used(
    dots,
    "ObjectProperty",
    "onClick:()=>u(a)",
    "actual direct dot selection",
  );
  used(
    dots,
    "ObjectPattern",
    "{count:d,selectedIndex:m,onSelect:u,className:f}",
    "dot count/state/callback consumer binding",
  );
  used(
    dots,
    "VariableDeclarator",
    "l=a===m",
    "dot selected state derives from selected index",
  );
  used(
    dots,
    "ObjectProperty",
    '"aria-current":l?"true":void 0',
    "selected dot accessibility state",
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
  assert.equal(
    rows.filter(
      (row) =>
        row.startsWith("116:I[31113,") && row.endsWith(',"LiveHomepage"]'),
    ).length,
    1,
  );
  const row = exactlyOne(
    rows.filter((row) => row.includes('"initialHeroData":')),
    "hero Flight row",
  );
  const value = JSON.parse(row.slice(row.indexOf(":") + 1));
  assert.equal(value[1][1], "$L116");
  const props = value[1][3];
  const hero = props.initialHeroData;
  assert.equal(hero.length, 6);
  const mints = hero.map((record) => record.mint);
  assert.equal(new Set(mints).size, 6);
  assert.ok(
    hero.every(
      (record) =>
        !Object.hasOwn(record, "id") && !Object.hasOwn(record, "linkUrl"),
    ),
  );
  const most = new Map(
    props.initialSectionData[0].map((record) => [record.mint, record]),
  );
  for (const record of hero) {
    const other = most.get(record.mint);
    assert.ok(other);
    for (const key of [
      "mint",
      "title",
      "symbol",
      "creator",
      "viewerCount",
      "isLive",
    ])
      assert.deepEqual(record[key], other[key]);
  }
  const slots = [
    ...capture.text.matchAll(/<div\b[^>]*data-testid="live-hero-slot"[^>]*>/gu),
  ].map((match) => match[0]);
  assert.equal(slots.length, 6);
  const selected = slots.map((slot) => slot.includes('data-selected="true"'));
  assert.deepEqual(selected, [true, false, false, false, false, false]);
  return {
    schemaVersion: 1,
    anchors: corpus.anchors,
    factories: factories.map((factory) => factory.provenance),
    witnesses,
    flight: {
      source: capture.record.path,
      sha256: capture.record.sha256,
      bytes: capture.bytes.length,
      capturedAt: corpus.manifest.captured_at,
      homepageReference: "$L116",
      rowId: row.slice(0, row.indexOf(":")),
      heroCount: 6,
      orderedMints: mints,
      orderedMintSha256: sha256(Buffer.from(JSON.stringify(mints))),
      mintIntersectionMostViewers: 6,
      rawHeroHasIdOrLinkUrl: false,
    },
    ssr: { slots: 6, selected },
    limits: [
      "Six existing archived identities, not six new streams.",
      "Selection arithmetic, initial state and direct-selection consumer recovered; no provider query, player/mute, financial calculation, current status or excluded coin action.",
      "Local buttons and metadata presentation adapt the observed selection lifecycle; no original visual/layout parity or feature credit.",
      "Captured JavaScript is never executed.",
    ],
  };
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const value = await recoverLiveHero();
  const text = `${JSON.stringify(value, null, 2)}\n`;
  if (process.argv.includes("--write")) await writeFile(contract, text);
  else
    assert.equal(
      await readFile(contract, "utf8"),
      text,
      "Live hero proof is stale",
    );
  console.log(
    "Verified six captured hero records, used initial/loop/direct selection and SSR slot state.",
  );
}
