import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-settings-decimal-input.mjs";
import { createSettingsDecimalInput } from "../reconstruction/settings-decimal-input/client.mjs";
const require = createRequire(
    new URL("../packages/frontend/package.json", import.meta.url),
  ),
  React = require("react"),
  runtime = require("react/jsx-runtime"),
  { c: useMemoCache } = require("react/compiler-runtime"),
  { renderToString } = require("react-dom/server");
function fixture(props = {}) {
  let input;
  const commits = [];
  const Component = createSettingsDecimalInput({
    ...runtime,
    useMemoCache,
    useState: React.useState,
    jsx(type, p, key) {
      if (type === "input") input = p;
      return runtime.jsx(type, p, key);
    },
  });
  const html = renderToString(
    runtime.jsx(Component, {
      value: 5,
      label: "Synthetic numeric value",
      onCommit: (value) => commits.push(value),
      ...props,
    }),
  );
  return {
    html,
    input,
    commits,
    change(value) {
      input.onChange({ currentTarget: { value } });
    },
  };
}
test("complete actual numeric input/grammar/frame and dispatcher conversion/callback boundary are source-authenticated", async () => {
  const c = await verify();
  assert.equal(c.retained.length, 3);
  assert.equal(c.witnesses.length, 4);
  assert.match(c.credit, /1872/);
  assert.match(c.capabilities ?? c.scope, /renderer/);
});
test("actual React SSR retains supplied value/label/min-independent text input/step/disabled/unit frame", () => {
  const f = fixture({
    value: 7.125,
    min: 10,
    step: 0.25,
    unit: "synthetic",
    isDisabled: true,
  });
  assert.equal(f.input.type, "text");
  assert.equal(f.input.inputMode, "decimal");
  assert.equal(f.input.value, "7.125");
  assert.equal(f.input.step, 0.25);
  assert.equal(f.input.disabled, true);
  assert.equal(f.input.autoComplete, "off");
  assert.equal(f.input.spellCheck, false);
  assert.equal(f.input["aria-label"], "Synthetic numeric value");
  assert.match(f.html, /synthetic/);
  assert.doesNotMatch(f.html, /<input[^>]*\bmin=/);
});
test("lexical comma normalization and12-code-unit bound precede immediate positive finite commits", () => {
  const f = fixture();
  for (const s of ["1,5", "1.25", "123456789012"]) f.change(s);
  assert.deepEqual(f.commits, [1.5, 1.25, 123456789012]);
  for (const s of [
    "1234567890123",
    "1,2,3",
    "1e3",
    "-2",
    "+3",
    " 4",
    "2a",
    "Infinity",
  ])
    f.change(s);
  assert.equal(f.commits.length, 3);
});
test("empty/dot/zero drafts do not commit; no max/step/rounding policy added", () => {
  const f = fixture({ step: 2 });
  for (const s of ["", ".", "0", "0.0"]) f.change(s);
  assert.deepEqual(f.commits, []);
  f.change(".25");
  f.change("0.001");
  assert.deepEqual(f.commits, [0.25, 0.001]);
});
test("minimum clamp happens after raw finite-positive check; malformed min preserved without new validation", () => {
  const f = fixture({ min: 2.5 });
  f.change("1");
  f.change("3");
  f.change("0");
  assert.deepEqual(f.commits, [2.5, 3]);
  const g = fixture({ min: NaN });
  g.change("1");
  assert.equal(g.commits.length, 1);
  assert.ok(Number.isNaN(g.commits[0]));
  const h = fixture({ min: -1 });
  h.change("0.5");
  assert.deepEqual(h.commits, [0.5]);
});
test("unvalidated controlled props stringify asoriginal ratherthan repaired numeric defaults", () => {
  assert.equal(fixture({ value: NaN }).input.value, "NaN");
  assert.equal(fixture({ value: -2 }).input.value, "-2");
  assert.equal(fixture({ value: 0 }).input.value, "0");
  assert.equal(fixture({ unit: "" }).html.includes("<span"), false);
});
test("synthetic commit callback failure propagates byidentity, with no new catch/rollback", () => {
  const failure = new Error("SYNTHETIC numeric commit denial"),
    f = fixture({
      onCommit() {
        throw failure;
      },
    });
  assert.throws(
    () => f.change("4"),
    (e) => e === failure,
  );
});
