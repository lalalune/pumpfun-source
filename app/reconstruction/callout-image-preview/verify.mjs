import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import prettier from 'prettier';
import { openCorpus, findNodes, exactlyOne, member, propertyName, sha256 } from '../../scripts/original-contracts/source.mjs';
import { normalizeSession } from '../../scripts/verify-search-session.mjs';

export const APP_ROOT = fileURLToPath(new URL('../..', import.meta.url));
export const DIRECTORY = 'reconstruction/callout-image-preview';
const HASHES = ['8e86c0d8ec8c4ede46d7fd8a949045c10ae434daf362f0bf26485fcf2504e094',
  '1eeb7e88c867c39e0e77454b5f5275beb50ee47351d8b9405305b613585b5e1b',
  'a4cb87e92ac156304798a162650e59347272e58057c65f60e52b6134d3fa06c1'];
const decls = (f) => f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : []);
function exported(f, id, name) {
  const call = exactlyOne(findNodes(f.node, (n) => n.type === 'CallExpression' && member(n.callee, f.runtime, 's') &&
    n.arguments[1]?.value === id && n.arguments[0]?.type === 'ArrayExpression' &&
    n.arguments[0].elements.some((x) => x?.value === name)), 'qualified bundled export ' + id + '.' + name);
  const values = call.arguments[0].elements, at = values.findIndex((n) => n?.value === name);
  assert.equal(values[at + 1].value, 0); return { call, value: values[at + 2] };
}
function namespaces(f) {
  const map = new Map();
  for (const d of decls(f)) {
    if (d.init?.type === 'CallExpression' && member(d.init.callee, f.runtime, 'i'))
      map.set(d.id.name, { id: d.init.arguments[0].value, root: d });
    else if (d.init?.type === 'Identifier' && map.has(d.init.name)) map.set(d.id.name, { ...map.get(d.init.name), alias: d });
    else map.delete(d.id.name);
  }
  return map;
}
const SPECS = {
  732486: { jsx: 'jsx', jsxs: 'jsxs' }, 445242: { c: 'useMemoCache' },
  352386: { useRef: 'React.useRef', useState: 'React.useState', useEffect: 'React.useEffect' },
  752365: { Trigger: 'HoverCard.Trigger', Portal: 'HoverCard.Portal', Positioner: 'HoverCard.Positioner', Popup: 'HoverCard.Popup', Root: 'HoverCard.Root' },
  458310: { default: 'Link' }, 360827: { V: 'CALLOUT_PREVIEW_CLASS' }, 338319: { c: 'classNames' },
};
const globals = Object.fromEntries(['Math', 'Symbol', 'document', 'window', 'Node'].map((n) => [n, 'global:' + n]));
// Lossless tuple representation for the reused comparator: retain every position,
// arity and an explicit marker. No array binding or instruction is omitted.
function tuples(node) {
  if (Array.isArray(node)) return node.map(tuples);
  if (!node || typeof node !== 'object') return node;
  if (node.type === 'ArrayPattern') {
    assert.ok(node.elements.every((n) => n && n.type !== 'RestElement'));
    return { type: 'ObjectPattern', previewTuplePattern: true, properties: node.elements.map((n, i) =>
      ({ type: 'ObjectProperty', key: { type: 'NumericLiteral', value: i }, value: tuples(n), computed: false, shorthand: false })) };
  }
  return Object.fromEntries(Object.entries(node).map(([k, v]) => [k, tuples(v)]));
}
function context(f, component) {
  const aliases = namespaces(f), qualified = {}, used = new Map();
  for (const n of findNodes(component, (n) => n.type === 'MemberExpression' && !n.computed &&
    n.object?.type === 'Identifier' && aliases.has(n.object.name))) {
    const provider = aliases.get(n.object.name), prop = propertyName(n.property), port = SPECS[provider.id]?.[prop];
    // A local variable may share an unrelated top-level namespace spelling.
    // Only the explicitly reviewed import/property pairs enter this map.
    if (port) { qualified[n.object.name + '.' + prop] = 'operation:' + provider.id + '.' + prop; used.set(n.object.name, provider); }
  }
  assert.deepEqual([...new Set([...used.values()].map((v) => v.id))].sort((a, b) => a - b), [338319, 352386, 360827, 445242, 458310, 732486, 752365]);
  const hover = Object.entries(qualified).filter(([, v]) => v.startsWith('operation:752365.'));
  assert.deepEqual(hover.map(([, v]) => v.split('.').at(-1)).sort(), ['Popup', 'Portal', 'Positioner', 'Root', 'Trigger']);
  return { used, qualified, normalized: normalizeSession(tuples(component), globals, qualified) };
}

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root), rows = corpus.index.modules.filter((m) => m.ids.includes(364889));
  assert.equal(rows.length, 3, 'all three image-owner variants must remain explicit');
  assert.deepEqual(rows.map((m) => m.sha256).sort(), [...HASHES].sort());
  const factories = [], frames = [], bindings = [];
  let canonical, source, component, ctx;
  for (const row of rows) for (const origin of row.origins) {
    const f = await corpus.factory(364889, { source: origin.source });
    const exp = exported(f, 364889, 'f'), value = exp.value, current = context(f, value);
    assert.equal(value.type, 'ArrowFunctionExpression');
    if (!canonical) { canonical = current.normalized; source = f; component = value; ctx = current; }
    else assert.deepEqual(current.normalized, canonical, 'complete image-owner frame variants differ');
    const allocation = exactlyOne(findNodes(value, (n) => n.type === 'CallExpression' && n.arguments[0]?.value === 35), 'actual 35-slot allocation');
    assert.ok(allocation.callee.type === 'SequenceExpression');
    factories.push(f.provenance); frames.push({ factory: f.provenance, frame: f.witness(value, 'complete35-slot image-preview owner'), normalizedSha256: sha256(JSON.stringify(current.normalized)) });
    for (const [name, provider] of current.used) {
      bindings.push({ alias: name, provider: provider.id, import: f.witness(provider.root, 'actual provider import'),
        ...(provider.alias ? { aliasBinding: f.witness(provider.alias, 'actual same-instance provider alias') } : {}) });
    }
    const library = exported(f, 752365, 'Root');
    bindings.push({ provider: 752365, registration: f.witness(library.call, 'bundled UI-library API registration, implementation external') });
  }
  assert.equal(factories.length, 3, 'selected physical origins remain bounded');
  const styles = corpus.index.modules.filter((m) => m.ids.includes(360827));
  assert.equal(styles.length, 1); assert.equal(styles[0].sha256, 'a7e8c373e26d211ce2321932e5e2bbe4d4e067de13ededbd31d7427932b8615e');
  const style = await corpus.factory(360827, { source: styles[0].origins[0].source });
  const styleCall = exactlyOne(findNodes(style.node, (n) => n.type === 'CallExpression' && member(n.callee, style.runtime, 's')), 'actual style export');
  const values = styleCall.arguments[0].elements, at = values.findIndex((n) => n?.value === 'V');
  assert.equal(values[at + 1].value, 0); const classValue = values[at + 2]; assert.equal(classValue.type, 'StringLiteral');
  const callerRows = corpus.index.modules.filter((m) => m.ids.includes(204478));
  assert.equal(callerRows.length, 1); assert.equal(callerRows[0].sha256, '27cc0223b79ff95cac02f490600cc4de894dee66af739beca525502c424dae3f');
  const caller = await corpus.factory(204478, { source: callerRows[0].origins[0].source });
  const callerImport = exactlyOne(decls(caller).filter((n) => n.init?.type === 'CallExpression' &&
    member(n.init.callee, caller.runtime, 'i') && n.init.arguments[0]?.value === 364889), 'actual media import');
  const calls = findNodes(caller.node, (n) => n.type === 'CallExpression' &&
    member(n.arguments[0], callerImport.id.name, 'f') && n.arguments[1]?.type === 'ObjectExpression');
  assert.equal(calls.length, 3, 'actual reply/update/main image handoffs');
  const callers = calls.map((n) => ({ call: caller.witness(n, 'actual image component invocation'),
    descriptor: caller.witness(n.arguments[1], 'complete original image prop descriptor') }));
  const declarations = [...ctx.used].map(([name, provider]) => provider.id === 752365 ? `${name}=HoverCard` :
    `${name}={${Object.entries(SPECS[provider.id]).map(([key, value]) => `${key}:${value}`).join(',')}}`).join(',');
  const text = await prettier.format(`
// Source-bound editable image owner; provider implementation and product mount are external.
export const CALLOUT_PREVIEW_CLASS=${style.text(classValue)};
export function createCalloutImagePreview({jsx,jsxs,useMemoCache,React,HoverCard,Link,classNames,document,window,Node}){
 for(const [name,value]of Object.entries({jsx,jsxs,useMemoCache,classNames,Node}))if(typeof value!=='function')throw new TypeError('Explicit image-preview capability required: '+name);
 for(const name of ['useRef','useState','useEffect'])if(typeof React?.[name]!=='function')throw new TypeError('Explicit React image-preview hook required: '+name);
 for(const name of ['Root','Trigger','Portal','Positioner','Popup'])if(HoverCard?.[name]==null)throw new TypeError('Explicit same-instance HoverCard component required: '+name);
 if(Link==null||!window||typeof document?.addEventListener!=='function'||typeof document?.removeEventListener!=='function')throw new TypeError('Explicit Link/viewport/document event capabilities required');
 const ${declarations};
 return ${source.text(component)};
}
`, { parser: 'babel' });
  return { text, provenance: { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a',
    scope: 'Complete364889 image-preview owning React frame through explicit actual UI-library and DOM capabilities; no product/native mount',
    anchors: corpus.anchors, factories, frames, bindings,
    style: { factory: style.provenance, literal: style.witness(classValue, 'only used360827.V constant') },
    caller: { factory: caller.provenance, import: caller.witness(callerImport, 'actual364889 image-owner dependency'), calls: callers },
    moduleSha256: sha256(Buffer.from(text)),
    ports: { HoverCard: 'Actual bundled752365 Root/Trigger/Portal/Positioner/Popup are one instance; alias chain and registration retained; library implementation external',
      React: 'Actual352386 useRef/useState/useEffect and445242.c compiler memo; explicit installed host capabilities',
      rendering: 'Actual732486 jsx/jsxs,338319.c class join and458310.default Link ports',
      DOM: 'Only source-used document scroll events, window viewport fields and Node identity; explicit caller realm; no storage/cookie acquisition' },
    limits: ['No captured factory is evaluated/imported; generated editable callbacks are the executable source adaptation',
      'No private UI-library timing/focus/collision/portal implementation, image service/remote reads/router execution or original product mount',
      'No video owner, composer/upload/action recovery, native/API/UI/pixel/security/full-runtime equivalence or feature/progress credit'] } };
}
export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  assert.equal(await readFile(path.join(root, DIRECTORY, 'client.mjs'), 'utf8'), result.text, 'image-preview module differs');
  assert.equal(await readFile(path.join(root, DIRECTORY, 'PROVENANCE.json'), 'utf8'), JSON.stringify(result.provenance, null, 2) + '\n', 'image-preview provenance differs');
  return result.provenance;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  assert.ok(process.argv.length === 3 && ['--write', '--check'].includes(process.argv[2]), 'Use --write|--check');
  if (process.argv[2] === '--write') {
    const r = await recover(); await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP_ROOT, DIRECTORY, 'client.mjs'), r.text);
    await writeFile(path.join(APP_ROOT, DIRECTORY, 'PROVENANCE.json'), JSON.stringify(r.provenance, null, 2) + '\n');
  } else await verify();
  console.log('PASS complete35-slot image owner, all3variants, same-instance UI API and3actual call sites');
}
