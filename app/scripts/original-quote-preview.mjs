// Parse authenticated inert factories. Captured JavaScript is never evaluated.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  objectProperty,
  propertyName,
  sha256,
} from "./original-contracts/source.mjs";
import { recoverMentionText } from "./original-mention-text.mjs";
const rootDefault = fileURLToPath(new URL("..", import.meta.url));
const output = "reconstruction/quote-preview/contract.json";
const require = (value, message) => {
  if (!value) throw Error(`Quote preview: ${message}`);
};
const target = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function exportsOf(factory) {
  const registration = exactlyOne(
    findNodes(
      factory.node,
      (n) =>
        n.type === "CallExpression" &&
        member(n.callee, factory.runtime, "s") &&
        (n.arguments[1]?.value === factory.id ||
          (n.arguments.length === 1 && factory.ids.length === 1)),
    ),
    `actual ${factory.id} export registration`,
  );
  const values = registration.arguments[0].elements,
    out = new Map();
  for (let i = 0; i < values.length; i += 3) {
    require(values[i]?.type === "StringLiteral" &&
      values[i + 1]?.value === 0 &&
      !out.has(values[i].value), "unsupported exports");
    out.set(values[i].value, values[i + 2]);
  }
  return out;
}
function resolve(factory, node) {
  if (node?.type !== "Identifier") return node;
  const defs = factory.node.body.body.flatMap((n) =>
    n.type === "VariableDeclaration"
      ? n.declarations
      : n.type === "FunctionDeclaration"
        ? [n]
        : [],
  );
  const def = exactlyOne(
    defs.filter((n) => n.id?.name === node.name),
    `top-level ${node.name}`,
  );
  return def.type === "FunctionDeclaration" ? def : def.init;
}
function bodyOf(factory) {
  let node = resolve(factory, exportsOf(factory).get("f"));
  if (
    node?.type === "CallExpression" &&
    propertyName(target(node.callee).property) === "memo"
  )
    node = resolve(factory, node.arguments[0]);
  require(["FunctionExpression", "ArrowFunctionExpression"].includes(
    node?.type,
  ), `actual ${factory.id}.f component`);
  return node;
}
function importBinding(factory, id) {
  return exactlyOne(
    findNodes(
      factory.node,
      (n) =>
        n.type === "VariableDeclarator" &&
        n.init?.type === "CallExpression" &&
        ["i", "r"].some((m) => member(n.init.callee, factory.runtime, m)) &&
        n.init.arguments[0]?.value === id,
    ),
    `actual import ${id}`,
  ).id.name;
}
function jsxCall(body, binding, name) {
  return exactlyOne(
    findNodes(
      body,
      (n) =>
        n.type === "CallExpression" && member(n.arguments[0], binding, name),
    ),
    `actual JSX ${binding}.${name}`,
  );
}
const pins = [
  {
    id: 386028,
    variants: [
      {
        sha256:
          "648d505abb256a21395a359f937f7746348b29815a4d99b7f7dd0e6a9ef23ada",
        source: "evidence/web/objects/caaf847d63c97cce.js",
      },
      {
        sha256:
          "dee84889b3994ca9401e340e546db2cdfe5cdedf866e8d07d90b8fc93e6945d6",
        source: "evidence/web/objects/57cc59637a8b8f78.js",
      },
      {
        sha256:
          "c3d3119ca74b30bcd58df0db07ec2879bdfd9bcc8e1998d547aa6c43434852f1",
        source: "evidence/web/objects/9535b69d76e2a69b.js",
      },
    ],
  },
  {
    id: 174251,
    variants: [
      {
        sha256:
          "c0467989c10ed4eee1b974863874d108285ab3dddb948799e042424a82ed2038",
        source: "evidence/web/objects/84bc29ea82bc5a21.js",
      },
    ],
  },
  {
    id: 349919,
    variants: [
      {
        sha256:
          "d9e37561efe6c7dfc134d7ace63aa44c5f74e6c406700bd925e0fb7cd4569bc6",
        source: "evidence/web/objects/91795a66d4097dbd.js",
      },
    ],
  },
  {
    id: 287129,
    variants: [
      {
        sha256:
          "75ce27324808ccd2b5cba5c591747c4c99cfdf42bc43ebdf06b5253c54a29ecb",
        source: "evidence/web/objects/84bc29ea82bc5a21.js",
      },
    ],
  },
  {
    id: 910976,
    variants: [
      {
        sha256:
          "b04bad164bee7eb5d2d522441333d604f8717335f346bbdddbf21da0218068c5",
        source: "evidence/web/objects/caaf847d63c97cce.js",
      },
      {
        sha256:
          "647dd0376ef663b6da340773b4a58769cc066c178d915beb73c09226e1476af3",
        source: "evidence/web/objects/57cc59637a8b8f78.js",
      },
      {
        sha256:
          "0738155da4af4202bbeedb9bab586bc4de7fb3b88758f8eff110c4db187377f5",
        source: "evidence/web/objects/9535b69d76e2a69b.js",
      },
    ],
  },
  {
    id: 365089,
    variants: [
      {
        sha256:
          "8957b61a69e89f0148cf9a43ca9bc4089cc0c2c892e476af960d1a02c966f4d1",
        source: "evidence/web/objects/ad7136d0b3a7f323.js",
      },
    ],
  },
];
export async function recoverQuotePreview(root = rootDefault) {
  const corpus = await openCorpus(root);
  require(corpus.anchors.manifestSha256 ===
    "9e0fc00719eb8c919dd4205d3c118eb48c4927e056c77e8343e26d6f7189bbb5", "unreviewed manifest");
  require(corpus.anchors.inventorySha256 ===
    "1d268ae7f2eb0f61eaaffd222269bf29d9ce06e9946372861721b2f159d868e2", "unreviewed inventory");
  const fragments = [],
    factories = new Map();
  const add = (f, node, label) => {
    const witness = f.witness(node, label);
    fragments.push({ ...witness, text: f.text(node) });
    return witness;
  };
  for (const pin of pins) {
    const variants = [];
    for (const spec of pin.variants) {
      const f = await corpus.factory(pin.id, { source: spec.source });
      require(f.provenance.sha256 ===
        spec.sha256, `unreviewed factory ${pin.id}`);
      variants.push(f);
    }
    factories.set(pin.id, variants);
  }
  // Parent1374 owns the actual registered174251.f -> memo(N) recovery.
  const mention = await recoverMentionText(root);
  require(JSON.stringify(mention, null, 2) + "\n" ===
    (await fs.readFile(
      path.join(root, "reconstruction/mention-text/contract.json"),
      "utf8",
    )), "parent1374 dependency is stale");
  require(mention.entry.export === "f" &&
    mention.entry.module === 174251, "wrong content export");
  const variants = [];
  for (const f of factories.get(386028)) {
    const body = bodyOf(f);
    const content = jsxCall(body, importBinding(f, 174251), "f");
    require(objectProperty(content.arguments[1], "content").property.name ===
      "text", "wrong text field");
    require(!content.arguments[1].properties.some(
      (n) => propertyName(n.key) === "withinLink",
    ), "non-default standalone path");
    const density = objectProperty(content.arguments[1], "density");
    require(density.type === "ConditionalExpression" &&
      density.consequent.value === "terminal" &&
      density.alternate.value === "comfortable", "wrong density branches");
    const shorten = exactlyOne(
      findNodes(
        body,
        (n) =>
          n.type === "CallExpression" &&
          member(target(n.callee), importBinding(f, 365089), "d"),
      ),
      "actual used shortener",
    );
    require(shorten.arguments[1]?.value === 4 &&
      shorten.arguments[2]?.value === 4, "not the4/4shortener");
    require(findNodes(
      body,
      (n) =>
        n.type === "StringLiteral" &&
        n.value === "profile.reposts.deleted_post",
    ).length === 1, "deleted key changed");
    require(findNodes(
      body,
      (n) => n.type === "StringLiteral" && n.value === "feed-quote-embed",
    ).length === 1, "blockquote changed");
    variants.push({
      factory: f.provenance,
      export: "f",
      body: add(
        f,
        body,
        "actual386028.f quote renderer, not390767.f route helper",
      ),
      content: add(f, content, "used174251.f content and density"),
      shortener: add(f, shorten, "used365089.d with4/4, notJ0x-specialcase"),
    });
  }
  const shortener = factories.get(365089)[0];
  add(
    shortener,
    resolve(shortener, exportsOf(shortener).get("d")),
    "365089.d full shortener; used4/4threshold9",
  );
  const adapter = factories.get(287129)[0];
  add(
    adapter,
    resolve(adapter, exportsOf(adapter).get("g")),
    "actual287129.g parent/callout envelope projection; NOT the new legacy seed join",
  );
  const consumers = [];
  for (const id of [349919, 910976])
    for (const f of factories.get(id)) {
      const body = bodyOf(f),
        call = jsxCall(body, importBinding(f, 386028), "f");
      const quoted = objectProperty(call.arguments[1], "quoted");
      require(quoted, "missing quoted prop");
      if (id === 349919) {
        require(quoted.type === "CallExpression" &&
          member(
            target(quoted.callee),
            importBinding(f, 287129),
            "g",
          ), "reply consumer bypasses287129.g");
        require(!call.arguments[1].properties.some(
          (n) => propertyName(n.key) === "dense",
        ), "standalone default no longer used");
      } else
        require(quoted.type === "MemberExpression" &&
          propertyName(quoted.property) ===
            "quoted", "callout quote envelope changed");
      consumers.push({
        module: id,
        export: "f",
        factory: f.provenance,
        invocation: add(
          f,
          call,
          id === 349919
            ? "actual quote branch consumes287129.g(row), omitsdense"
            : "actual callout quote branch passesquoted envelope plusdense; not reconstructed coordinator",
        ),
      });
    }
  const implementation = [];
  for (const file of [
    "reconstruction/quote-preview/model.mjs",
    "reconstruction/quote-preview/model.d.mts",
    "packages/frontend/src/components/feed/QuotePreview.tsx",
    "packages/frontend/src/components/feed/LocalQuoteRow.tsx",
    "packages/frontend/src/components/feed/quote-preview.module.css",
    "packages/frontend/src/components/feed/feed-data.ts",
    "packages/frontend/src/components/feed/feed-snapshot.ts",
    "packages/frontend/src/components/feed/FeedList.tsx",
    "packages/frontend/src/app/page.tsx",
  ])
    implementation.push({
      path: file,
      sha256: sha256(await fs.readFile(path.join(root, file))),
    });
  return {
    schemaVersion: 1,
    authority: "Authenticated inert AST ranges; captured JS never evaluated",
    inputs: corpus.anchors,
    entry: { module: 386028, export: "f", variants },
    dependencies: {
      mentionText: {
        pullRequest: 1374,
        publicHead: "7f1f6627b8e3aae1d7e4a9c99c2652202549a0cd",
        entry: mention.entry,
        contractSha256: sha256(
          await fs.readFile(
            path.join(root, "reconstruction/mention-text/contract.json"),
          ),
        ),
        credit: "Prerequisite; zero new recovery credit",
      },
      shortener: shortener.provenance,
      originalEnvelopeProjection: adapter.provenance,
    },
    consumers,
    implementedSurface: {
      dense: false,
      withinLink: false,
      density: "comfortable",
      mountedIn:
        "Home local examples only; default profile/root projection unchanged",
    },
    translation: {
      knownKey: "profile.reposts.deleted_post",
      originalEnglishCopy: "unknown in retained inputs",
      localInjectedCopy: "Quoted local record unavailable",
    },
    localAdaptation: {
      authority:
        "NEW authored opt-in legacy seed join; not recovered original API/coordinator/visibility semantics",
      targets:
        "visible recorded target content with resolved optional local name/address; hidden/deleted/missing targets withheld",
      reposts: "excluded",
      defaults: "validateLocalFeed remains root-only unless includeQuotes:true",
    },
    implementation,
    fragments,
    limits: [
      "Original actual consumer bindings do not establish a unique running variant or a full original route",
      "Only standalone comfortable path exposed; terminal/dense and original CSS/pixel/translation parity not claimed",
      "LegacyPostsStore seed joining is NEW local host adaptation, not original287129.g behavior",
      "No backend API, auth, session, mutation, real identity, repost action/count, feature/milestone or compatibility credit",
    ],
  };
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !["--write", "--check"].includes(mode))
    throw Error("usage: original-quote-preview.mjs --write|--check");
  const value = JSON.stringify(await recoverQuotePreview(), null, 2) + "\n",
    destination = path.join(rootDefault, output);
  if (mode === "--write") await fs.writeFile(destination, value);
  else if ((await fs.readFile(destination, "utf8")) !== value)
    throw Error("Quote preview artifact is stale");
  console.log(
    `${mode === "--write" ? "Wrote" : "Verified"} original standalone quote preview`,
  );
}
