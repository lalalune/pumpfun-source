import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import test from "node:test";
import { parse } from "@babel/parser";
import ts from "typescript";
const requireFrontend = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = requireFrontend("react");
const { renderToStaticMarkup } = requireFrontend("react-dom/server");
const app = fileURLToPath(new URL("../", import.meta.url));
const program = `import hashlib, html, importlib.util, sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('icons',Path('scripts/extract-shell-icons.py'))
icons=importlib.util.module_from_spec(spec);spec.loader.exec_module(icons)
_,body=icons.captured(icons.manifest()['records'],icons.HOME)
segment=icons.shell_segment(body.decode('utf-8'))
svg=icons.SVG.findall(segment)[1]
svg=svg.replace('<svg ', '<svg aria-label="'+html.escape(sys.argv[1],quote=True)+'" ',1)
sys.stdout.buffer.write(icons.component('Probe',svg,'retained NavHomeIcon with isolated static label').encode('utf-8'))
`;
function generated(label) {
  const result = spawnSync(
    process.env.PYTHON || "python",
    ["-c", program, label],
    { cwd: app, encoding: "utf8" },
  );
  assert.equal(result.status, 0, result.stderr);
  parse(result.stdout, {
    sourceType: "module",
    plugins: ["typescript", "jsx"],
  });
  const compiled = ts.transpileModule(result.stdout, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.React,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  // This executes only our generated static presentational component, never
  // the retained application's scripts or factory bodies.
  const exports = {};
  vm.runInNewContext(compiled, { exports, React });
  return exports.Probe;
}
for (const label of [
  "搜索",
  'say "hi"',
  "a\nb",
  "a>b",
  "back\\slash",
  "& < >",
]) {
  test(`generated retained icon preserves ${JSON.stringify(label)} and props override`, () => {
    const Probe = generated(label);
    const expected = renderToStaticMarkup(
      React.createElement("svg", { "aria-label": label }),
    ).match(/aria-label="[^"]*"/)[0];
    const rendered = renderToStaticMarkup(React.createElement(Probe));
    assert.ok(rendered.includes(expected), rendered);
    assert.ok(rendered.includes("<path"), "retained vector content is present");
    const overridden = renderToStaticMarkup(
      React.createElement(Probe, {
        "aria-label": "override",
        "data-probe": "ok",
      }),
    );
    assert.ok(overridden.includes('aria-label="override"'), overridden);
    assert.ok(overridden.includes('data-probe="ok"'), overridden);
  });
}
