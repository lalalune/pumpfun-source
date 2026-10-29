import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { parse } from "@babel/parser";
import {
  openCorpus,
  findNodes,
  exactlyOne,
  member,
  sha256,
} from "../../scripts/original-contracts/source.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, "../..");
const corpus = await openCorpus(APP);
const pins = [
  [
    590407,
    "evidence/web/objects/2fe17dced92b840b.js",
    "3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda",
  ],
  [
    706615,
    "evidence/web/objects/c3601a995a6b7f37.js",
    "e606b2e7f5ab2bfd5da0abb70db2de0560f01d4d131d156719d8623614219e74",
  ],
  [
    139209,
    "evidence/web/objects/2b47dd0b38a1608f.js",
    "8d4ffb7afbfae1b99df53cf4d8421f1fb6f85c290468471f2e4f71f58358ed9b",
  ],
];
const factories = [];
for (const [id, source, hash] of pins) {
  const factory = await corpus.factory(id, { source });
  assert.equal(
    factory.provenance.sha256,
    hash,
    "reviewed source context changed",
  );
  factories.push(factory);
}
const [page, helpers, declarations] = factories;
const get = (factory, name) =>
  exactlyOne(
    findNodes(
      factory.node,
      (node) => node.type === "VariableDeclarator" && node.id.name === name,
    ),
    `actual declaration ${name}`,
  );
const call = (node, binding, property, firstArgument) =>
  exactlyOne(
    findNodes(node, (entry) => {
      if (entry.type !== "CallExpression") return false;
      const callee =
        entry.callee.type === "SequenceExpression"
          ? entry.callee.expressions.at(-1)
          : entry.callee;
      return (
        member(callee, binding, property) &&
        (firstArgument === undefined ||
          entry.arguments[0]?.name === firstArgument)
      );
    }),
    `actual call ${binding}.${property}(${firstArgument ?? "..."})`,
  );
const board = exactlyOne(
  page.node.body.body.filter(
    (node) => node.type === "FunctionDeclaration" && node.id.name === "to",
  ),
  "actual board",
);
const hero = get(page, "e$");
const copy = get(page, "eL");
const boardHero = call(board, "a", "jsx", "e$");
const heroCopy = call(hero, "a", "jsx", "eL");
const select = call(copy, "$", "H");
const render = call(copy, "a", "jsx", "ee");
const prop = (callNode, name) =>
  exactlyOne(
    callNode.arguments[1].properties.filter(
      (node) => node.type === "ObjectProperty" && node.key.name === name,
    ),
    `actual ${name} prop`,
  ).value;
assert.equal(prop(boardHero, "competition").name, "R");
assert.equal(prop(heroCopy, "competition").name, "z");
assert.equal(select.arguments[0].name, "h");
assert.equal(prop(render, "target").name, "j");
const importHelper = exactlyOne(
  findNodes(
    page.node,
    (node) =>
      node.type === "VariableDeclarator" &&
      node.id.name === "$" &&
      node.init?.type === "CallExpression" &&
      member(node.init.callee, page.runtime, "i") &&
      node.init.arguments[0]?.value === 706615,
  ),
  "actual $.H helper import",
);
const exportedTarget = exactlyOne(
  findNodes(
    helpers.node,
    (node) =>
      node.type === "CallExpression" &&
      member(node.callee, helpers.runtime, "s"),
  ),
  "actual helper exports",
).arguments[0].elements;
const targetIndex = exportedTarget.findIndex((node) => node.value === "H");
assert.ok(targetIndex >= 0);
const target = exportedTarget[targetIndex + 2];
const dto = get(declarations, "b");
const witnesses = [
  page.witness(
    board,
    "complete actual selected-competition board consumer; no whole-component recovery claim",
  ),
  page.witness(hero, "complete actual hero consumer"),
  page.witness(copy, "complete actual hero-copy consumer"),
  page.witness(boardHero, "board renders hero with selected competition"),
  page.witness(heroCopy, "hero renders copy with the same competition"),
  page.witness(
    importHelper,
    "actual import of 706615 for phase/time selection",
  ),
  page.witness(
    select,
    "hero copy selects target directly from competition DTO",
  ),
  page.witness(
    render,
    "hero copy renders accepted countdown with selected target",
  ),
  helpers.witness(
    target,
    "complete original phase/time selector; accepted component dependency",
  ),
];
for (const name of ["phase", "startsAt", "endsAt"]) {
  witnesses.push(
    declarations.witness(
      exactlyOne(
        findNodes(
          dto.init,
          (node) => node.type === "ObjectProperty" && node.key?.name === name,
        ),
        `declared DTO ${name}`,
      ),
      `actual competition DTO ${name}`,
    ),
  );
}
const adapter =
  "packages/frontend/src/components/leaderboard/CompetitionCountdown.tsx";
const display =
  "packages/frontend/src/components/leaderboard/original-countdown.mjs";
const result = {
  schema: 1,
  scope:
    "Selected competition detail caller reuses the accepted source-adapted countdown; no adapter or server-phase calculation change",
  provenance: factories.map((factory) => factory.provenance),
  witnesses,
  dependencies: Object.fromEntries(
    await Promise.all(
      [adapter, display].map(async (name) => [
        name,
        sha256(await readFile(path.join(APP, name))),
      ]),
    ),
  ),
  mapping:
    "Documented native CompetitionDetailData.competition exposes phase/startsAt/endsAt and is admitted before detail rendering. Pass that object unchanged to the existing CompetitionCountdown adapter. Original to→e$→eL→706615.H→ee supports displaying the countdown for the selected board, not only a list card.",
  limits: [
    "Accepted #894 supplies the complete editable display, digit boxes, selector and timer; this unit claims only the missing mounted caller.",
    "Open #1652 owns countdown expiry adapter behavior; no adapter, selector, clock, phase, API, ranking, auth, promotion or financial policy is changed here.",
    "The local English labels and native detail page are explicit adapters. Original hero video, provider, cache, full-layout and production-API parity are not claimed.",
  ],
};
const record = path.join(HERE, "source-evidence.json");
if (process.argv.includes("--write")) {
  await writeFile(record, JSON.stringify(result, null, 2) + "\n");
} else {
  assert.deepEqual(JSON.parse(await readFile(record, "utf8")), result);
}
if (!process.argv.includes("--source-only")) {
  const client = parse(
    await readFile(
      path.join(
        APP,
        "packages/frontend/src/app/leaderboard/leaderboard-client.tsx",
      ),
      "utf8",
    ),
    { sourceType: "module", plugins: ["typescript", "jsx"] },
  );
  const detail = exactlyOne(
    findNodes(
      client,
      (node) =>
        node.type === "JSXElement" &&
        node.openingElement.name.name === "div" &&
        node.openingElement.attributes.some(
          (attribute) =>
            attribute.type === "JSXAttribute" &&
            attribute.name.name === "className" &&
            attribute.value?.value === "competition-detail-heading",
        ),
    ),
    "native admitted detail heading",
  );
  exactlyOne(
    findNodes(
      client,
      (node) =>
        node.type === "IfStatement" &&
        findNodes(
          node.test,
          (part) =>
            part.type === "StringLiteral" &&
            part.value === "competition-detail",
        ).length === 1 &&
        findNodes(node.consequent, (part) => part === detail).length === 1,
    ),
    "detail consumer remains behind the admitted competition-detail branch",
  );
  const countdown = exactlyOne(
    findNodes(
      detail,
      (node) =>
        node.type === "JSXOpeningElement" &&
        node.name.name === "CompetitionCountdown",
    ),
    "native selected-detail countdown caller",
  );
  const prop = exactlyOne(
    countdown.attributes.filter(
      (node) =>
        node.type === "JSXAttribute" && node.name.name === "competition",
    ),
    "competition prop",
  );
  assert.ok(member(prop.value.expression, "data", "competition"));
}
console.log(
  "Verified original selected-board countdown caller closure and unchanged accepted display/selector; no provider/API parity claim",
);
