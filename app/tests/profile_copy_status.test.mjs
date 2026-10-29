import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { parse } from "@babel/parser";

// Execute only the maintained callback with synthetic ports; no DOM/browser,
// clipboard, captured bundle or SDK is executed. This does not test React mounts.
const source = fs.readFileSync(
  new URL(
    "../packages/frontend/src/components/profile/CopyAddressButton.tsx",
    import.meta.url,
  ),
  "utf8",
);
const ast = parse(source, {
  sourceType: "module",
  plugins: ["typescript", "jsx"],
});
const component = ast.program.body.find(
  (n) =>
    n.type === "ExportNamedDeclaration" &&
    n.declaration?.id?.name === "CopyAddressButton",
).declaration;
const callback = component.body.body.find(
  (n) => n.type === "FunctionDeclaration" && n.id.name === "copyAddress",
);
const body = source.slice(callback.start, callback.end);
function deferred() {
  let resolve, reject;
  const promise = new Promise((a, b) => {
    resolve = a;
    reject = b;
  });
  return { promise, resolve, reject };
}
function harness() {
  const writes = [];
  const pending = [];
  const statuses = [];
  const request = { current: 0 };
  const navigator = {
    clipboard: {
      writeText: (address) => {
        writes.push(address);
        const d = deferred();
        pending.push(d);
        return d.promise;
      },
    },
  };
  const setStatus = (status) => statuses.push(status);
  const setOutcome = (outcome) => statuses.push(outcome?.status ?? "idle");
  const copy = Function(
    "navigator",
    "setStatus",
    "setOutcome",
    "request",
    "address",
    `return (${body})`,
  )(navigator, setStatus, setOutcome, request, "public-address");
  return { copy, writes, pending, statuses };
}

test("older failure must not overwrite newer successful copy feedback", async () => {
  const h = harness();
  const old = h.copy();
  const latest = h.copy();
  h.pending[1].resolve();
  await latest;
  assert.equal(h.statuses.at(-1), "copied");
  h.pending[0].reject(new Error("older denied"));
  await old;
  assert.equal(h.statuses.at(-1), "copied");
  assert.deepEqual(h.writes, ["public-address", "public-address"]);
});

test("older success must not overwrite newer failed copy feedback", async () => {
  const h = harness();
  const old = h.copy();
  const latest = h.copy();
  h.pending[1].reject(new Error("latest denied"));
  await latest;
  assert.equal(h.statuses.at(-1), "failed");
  h.pending[0].resolve();
  await old;
  assert.equal(h.statuses.at(-1), "failed");
});

test("a new copy attempt clears previous feedback while pending", async () => {
  const h = harness();
  const first = h.copy();
  h.pending[0].resolve();
  await first;
  assert.equal(h.statuses.at(-1), "copied");
  const second = h.copy();
  assert.equal(h.statuses.at(-1), "idle");
  h.pending[1].reject(new Error("denied"));
  await second;
  assert.equal(h.statuses.at(-1), "failed");
});

test("feedback projection hides results belonging to a different address", () => {
  const declaration = component.body.body
    .filter((node) => node.type === "VariableDeclaration")
    .flatMap((node) => node.declarations)
    .find((node) => node.id.name === "status");
  assert.ok(declaration?.init, "address-bound feedback projection exists");
  const expression = source.slice(declaration.init.start, declaration.init.end);
  const project = Function("outcome", "address", `return (${expression})`);
  assert.equal(project(null, "new-address"), "idle");
  assert.equal(
    project({ address: "old-address", status: "copied" }, "new-address"),
    "idle",
  );
  assert.equal(
    project({ address: "new-address", status: "failed" }, "new-address"),
    "failed",
  );
});
