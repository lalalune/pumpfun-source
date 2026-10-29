import { readFile } from "node:fs/promises";
import { parse } from "@babel/parser";
import {
  decodeSource,
  exactlyOne,
  findNodes,
  sha256,
} from "../../scripts/original-contracts/source.mjs";

const path = "packages/frontend/src/components/shell/search/SearchDialog.tsx";
const bytes = await readFile(new URL(`../../${path}`, import.meta.url));
const { text, byteOffsets } = decodeSource(bytes);
const ast = parse(text, {
  sourceType: "module",
  plugins: ["typescript", "jsx"],
});
function record(node, label) {
  return {
    label,
    path,
    sourceSha256: sha256(bytes),
    utf16: [node.start, node.end],
    utf8: [byteOffsets[node.start], byteOffsets[node.end]],
    sha256: sha256(
      bytes.subarray(byteOffsets[node.start], byteOffsets[node.end]),
    ),
    text: text.slice(node.start, node.end),
  };
}
const pick = (predicate, label) =>
  record(exactlyOne(findNodes(ast, predicate), label), label);
const witnesses = [
  pick(
    (node) =>
      node.type === "CallExpression" &&
      node.callee.name === "useEffect" &&
      text.slice(node.start, node.end).includes("completedClear"),
    "actual query-commit effect",
  ),
  pick(
    (node) =>
      node.type === "FunctionDeclaration" && node.id.name === "onSubmit",
    "actual submit close and push",
  ),
  pick(
    (node) => node.type === "JSXAttribute" && node.name.name === "onChange",
    "actual input edit setter",
  ),
  pick(
    (node) =>
      node.type === "VariableDeclarator" && node.id.name === "currentQuery",
    "actual URL query snapshot",
  ),
  pick(
    (node) =>
      node.type === "VariableDeclarator" && node.id.name === "onPopState",
    "actual native history cleanup",
  ),
];
const intent = findNodes(
  ast,
  (node) =>
    node.type === "VariableDeclarator" && node.id.name === "pendingSubmit",
);
if (intent.length)
  witnesses.push(
    record(
      exactlyOne(intent, "submission intent"),
      "actual submission intent ref",
    ),
  );
console.log(
  JSON.stringify(
    {
      method:
        "Static maintained input/URL/ref dataflow; not original Pump scheduling or native parity",
      witnesses,
    },
    null,
    2,
  ),
);
