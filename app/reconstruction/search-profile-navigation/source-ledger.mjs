import { readFile } from "node:fs/promises";
import { parse } from "@babel/parser";
import {
  decodeSource,
  exactlyOne,
  findNodes,
  sha256,
} from "../../scripts/original-contracts/source.mjs";

const root = new URL("../../", import.meta.url);
async function source(path) {
  const bytes = await readFile(new URL(path, root));
  const { text, byteOffsets } = decodeSource(bytes);
  const ast = parse(text, {
    sourceType: "unambiguous",
    plugins: ["typescript", "jsx"],
  });
  const witness = (node, label) => ({
    label,
    path,
    sourceSha256: sha256(bytes),
    utf16: [node.start, node.end],
    utf8: [byteOffsets[node.start], byteOffsets[node.end]],
    sha256: sha256(
      bytes.subarray(byteOffsets[node.start], byteOffsets[node.end]),
    ),
    text: text.slice(node.start, node.end),
  });
  return { ast, witness };
}
const local = await source(
  "packages/frontend/src/components/shell/search/LocalUserSearch.tsx",
);
const dialog = await source(
  "packages/frontend/src/components/shell/search/SearchDialog.tsx",
);
const framework = await source(
  "packages/frontend/node_modules/next/dist/client/app-dir/link.js",
);
const resultLink = exactlyOne(
  findNodes(
    local.ast,
    (node) => node.type === "JSXOpeningElement" && node.name.name === "Link",
  ),
  "local result Link",
);
const closeCallback = exactlyOne(
  findNodes(
    dialog.ast,
    (node) => node.type === "JSXAttribute" && node.name.name === "onNavigate",
  ),
  "dialog result-navigation callback",
);
const frameworkFunction = (name) =>
  exactlyOne(
    findNodes(
      framework.ast,
      (node) => node.type === "FunctionDeclaration" && node.id.name === name,
    ),
    name,
  );
const click = exactlyOne(
  findNodes(
    framework.ast,
    (node) => node.type === "ObjectMethod" && node.key.name === "onClick",
  ),
  "actual Next Link click dispatcher",
);
const docsPath =
  "packages/frontend/node_modules/next/dist/docs/01-app/03-api-reference/02-components/link.md";
const docs = await readFile(new URL(docsPath, root));
const pkg = JSON.parse(
  await readFile(
    new URL("packages/frontend/node_modules/next/package.json", root),
  ),
);
console.log(
  JSON.stringify(
    {
      method:
        "Static maintained caller/callback and installed framework dataflow; not original Pump modifier-behavior equivalence",
      localResult: local.witness(
        resultLink,
        "actual result Link opening element",
      ),
      modalCallback: dialog.witness(
        closeCallback,
        "actual parent dialog-close callback",
      ),
      framework: {
        version: pkg.version,
        docs: { path: docsPath, sha256: sha256(docs) },
        click: framework.witness(
          click,
          "onClick runs before navigation admission",
        ),
        modifier: framework.witness(
          frameworkFunction("isModifiedEvent"),
          "actual modifier admission",
        ),
        navigation: framework.witness(
          frameworkFunction("linkClicked"),
          "modifier early return before onNavigate",
        ),
      },
    },
    null,
    2,
  ),
);
