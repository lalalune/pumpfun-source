// Authenticate inert original factories; never import or evaluate captured JS.
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
  literal,
  sha256,
} from "./original-contracts/source.mjs";

const rootDefault = fileURLToPath(new URL("..", import.meta.url));
const output = "reconstruction/mention-text/contract.json";
const object = (name) => `evidence/web/objects/${name}`;
const require = (condition, reason) => {
  if (!condition) throw Error(`Mention text: ${reason}`);
};
const target = (node) =>
  node?.type === "SequenceExpression" ? node.expressions.at(-1) : node;
function exportsOf(factory) {
  const registration = exactlyOne(
    findNodes(
      factory.node,
      (node) =>
        node.type === "CallExpression" &&
        member(node.callee, factory.runtime, "s") &&
        (node.arguments[1]?.value === factory.id ||
          (node.arguments.length === 1 && factory.ids.length === 1)),
    ),
    `actual ${factory.id} export registration`,
  );
  const result = new Map(),
    values = registration.arguments[0].elements;
  for (let i = 0; i < values.length; i += 3) {
    require(values[i]?.type === "StringLiteral" &&
      values[i + 1]?.value === 0 &&
      !result.has(values[i].value), "unsupported exports");
    result.set(values[i].value, values[i + 2]);
  }
  return result;
}
function resolve(factory, node) {
  if (node.type !== "Identifier") return node;
  const definitions = factory.node.body.body.flatMap((statement) =>
    statement.type === "VariableDeclaration"
      ? statement.declarations
      : statement.type === "FunctionDeclaration"
        ? [statement]
        : [],
  );
  const definition = exactlyOne(
    definitions.filter((n) => n.id?.name === node.name),
    `top-level ${node.name}`,
  );
  return definition.type === "FunctionDeclaration"
    ? definition
    : definition.init;
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
function calls(node, binding, name) {
  return findNodes(
    node,
    (n) =>
      n.type === "CallExpression" && member(target(n.callee), binding, name),
  );
}

export async function recoverMentionText(root = rootDefault) {
  const corpus = await openCorpus(root);
  require(corpus.anchors.manifestSha256 ===
    "9e0fc00719eb8c919dd4205d3c118eb48c4927e056c77e8343e26d6f7189bbb5", "unreviewed manifest");
  require(corpus.anchors.inventorySha256 ===
    "1d268ae7f2eb0f61eaaffd222269bf29d9ce06e9946372861721b2f159d868e2", "unreviewed inventory");
  const specs = [
    [
      314012,
      "84bc29ea82bc5a21.js",
      "3a92f88a738a1973b7255ddc6fc6bcb33c1984e442065ce184b785368e5861dc",
    ],
    [
      174251,
      "84bc29ea82bc5a21.js",
      "c0467989c10ed4eee1b974863874d108285ab3dddb948799e042424a82ed2038",
    ],
    [
      146695,
      "fd402d4185b44ce9.js",
      "bb995bc856796eb404e21763f5a72275af2b0efa06b46f0d12507e1c6a3d90a1",
    ],
  ];
  const factories = [];
  for (const [id, source, hash] of specs) {
    const factory = await corpus.factory(id, { source: object(source) });
    require(factory.provenance.sha256 === hash, `unreviewed factory ${id}`);
    factories.push(factory);
  }
  const [mention, renderer, profile] = factories;
  const fragments = [],
    add = (f, node, label) => {
      const witness = f.witness(node, label);
      fragments.push({ ...witness, text: f.text(node) });
      return witness;
    };
  const parser = resolve(mention, exportsOf(mention).get("m"));
  const registration = exportsOf(renderer).get("f");
  const memo = resolve(renderer, registration);
  require(memo.type === "CallExpression" &&
    propertyName(target(memo.callee).property) ===
      "memo", "renderer no longer memo component");
  const component = memo.arguments[0];
  const input = component.params[0];
  const defaults = new Map(
    input.properties
      .filter((n) => n.value?.type === "AssignmentPattern")
      .map((n) => [propertyName(n.key), literal(n.value.right)]),
  );
  require(defaults.get("withinLink") === false &&
    defaults.get("density") === "comfortable", "default surface changed");
  const parserCalls = exactlyOne(
    calls(renderer.node, importBinding(renderer, 314012), "m"),
    "used mention parser",
  );
  const pathCall = exactlyOne(
    calls(renderer.node, importBinding(renderer, 146695), "$"),
    "used profile path formatter",
  );
  const property = exactlyOne(
    findNodes(
      renderer.node,
      (n) => n.type === "ObjectProperty" && propertyName(n.key) === "prefetch",
    ),
    "mention prefetch override",
  );
  require(literal(property.value) === false, "mention started prefetching");
  const href = resolve(profile, exportsOf(profile).get("$"));
  add(
    mention,
    parser,
    "314012.m serialized mention parsing; ASCII username and loose 36-character ID",
  );
  add(
    renderer,
    renderer.node,
    "174251.f complete source context; implemented default standalone comfortable path only",
  );
  add(renderer, parserCalls, "actual parser invocation before tweet splitting");
  add(renderer, pathCall, "actual mention userId to profile href");
  add(
    profile,
    href,
    "146695.$ route formatter; only its used string input branch is implemented here",
  );
  const consumers = [];
  for (const [source, hash] of [
    [
      "caaf847d63c97cce.js",
      "648d505abb256a21395a359f937f7746348b29815a4d99b7f7dd0e6a9ef23ada",
    ],
    [
      "57cc59637a8b8f78.js",
      "dee84889b3994ca9401e340e546db2cdfe5cdedf866e8d07d90b8fc93e6945d6",
    ],
    [
      "9535b69d76e2a69b.js",
      "c3d3119ca74b30bcd58df0db07ec2879bdfd9bcc8e1998d547aa6c43434852f1",
    ],
  ]) {
    const consumer = await corpus.factory(386028, { source: object(source) });
    require(consumer.provenance.sha256 === hash, "unreviewed consumer variant");
    const body = resolve(consumer, exportsOf(consumer).get("f"));
    const binding = importBinding(consumer, 174251);
    const invocation = exactlyOne(
      findNodes(
        body,
        (n) =>
          n.type === "CallExpression" &&
          n.arguments[0]?.type === "MemberExpression" &&
          member(n.arguments[0], binding, "f"),
      ),
      "actual standalone renderer consumer",
    );
    const props = invocation.arguments[1];
    require(objectProperty(props, "content") &&
      !props.properties.some(
        (n) => propertyName(n.key) === "withinLink",
      ), "consumer no longer uses default standalone path");
    consumers.push({
      module: 386028,
      factory: consumer.provenance,
      invocation: add(
        consumer,
        invocation,
        "386028.f renders post/repost preview text with default standalone renderer",
      ),
      ambiguity:
        "All three captured physical variants retained; no running variant is selected",
    });
  }
  const css = await corpus.capture(object("4a341ff6a9551721.css"));
  const token = "--greentext:74 222 128";
  const position = css.text.indexOf(token);
  require(position >= 0 &&
    css.text.indexOf(token, position + 1) === -1, "greentext token changed");
  const color = css.witness(
    { start: position, end: position + token.length },
    "captured greentext theme token",
  );
  fragments.push({ ...color, text: token });
  const implementation = [];
  for (const file of [
    "reconstruction/mention-text/model.mjs",
    "reconstruction/mention-text/model.d.mts",
    "packages/frontend/src/components/feed/MentionText.tsx",
    "packages/frontend/src/components/feed/mention-text.module.css",
    "packages/frontend/src/components/feed/FeedItem.tsx",
    "packages/frontend/src/components/feed/NativeCalloutFeed.tsx",
  ])
    implementation.push({
      path: file,
      sha256: sha256(await fs.readFile(path.join(root, file))),
    });
  return {
    schemaVersion: 1,
    authority:
      "Authenticated inert AST/CSS ranges; captured JS never evaluated",
    inputs: corpus.anchors,
    entry: {
      module: 174251,
      export: "f",
      displayName: "MentionText",
      factory: renderer.provenance,
    },
    dependencies: factories
      .filter((f) => f.id !== 174251)
      .map((f) => f.provenance),
    consumers,
    implementedSurface: {
      withinLink: false,
      density: "comfortable",
      renderedIn: ["FeedItem.content", "NativeCalloutCard.thesis"],
    },
    behavior: {
      mentionUsername: "ASCII letters/digits/underscore, length1..15",
      mentionUserId:
        "Exactly36 hex-or-hyphen characters; not strict UUID validation",
      mentionHref:
        "/profile/ plus encoded original userId; no ownership/profile-existence assertion",
      tweet:
        "HTTP(S) URL candidate → URL parse → one optional hostname prefix before x.com/twitter.com → username/status/digit-prefix path; trailing punctuation stays text",
      plainUrls:
        "Other URLs stay plain text, with no auto embed or network fetch",
      greentext:
        "A line starts with spaces/tabs then >; split by LF only when any such line exists, retaining line breaks and CR",
      click:
        "Standalone mention and external status anchors stop propagation; prefetchfalse or target_blank/noopener/noreferrer",
    },
    implementation,
    fragments,
    limits: [
      "Standalone comfortable path only; withinLink button/router and terminal-density styling are not exposed or claimed",
      "Source SVG icon is replaced by an aria-hidden text glyph; authored CSS fits existing local feed; no original pixel parity",
      "146695 path source and shared authentication/range tools are existing dependencies with zero new recovery credit",
      "No composer/query/auth/session/backend operation/identity/mutation/feature-ledger/API-compatibility claim",
      "Source consumers establish actual call bindings, not complete original rendered route reachability",
    ],
  };
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !["--write", "--check"].includes(mode))
    throw Error("usage: original-mention-text.mjs --write|--check");
  const value = JSON.stringify(await recoverMentionText(), null, 2) + "\n";
  const destination = path.join(rootDefault, output);
  if (mode === "--write") await fs.writeFile(destination, value);
  else if ((await fs.readFile(destination, "utf8")) !== value)
    throw Error("Mention text artifact is stale");
  console.log(
    `${mode === "--write" ? "Wrote" : "Verified"} original standalone mention text`,
  );
}
