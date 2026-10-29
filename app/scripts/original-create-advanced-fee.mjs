import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, propertyName, objectProperty, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = fileURLToPath(new URL('..', import.meta.url));
export const CLIENT = 'reconstruction/create-advanced-fee/client.mjs';
export const CONTRACT = 'reconstruction/create-advanced-fee/contract.json';
const EXPECTED = [
  [734638, '89ce7de3b9bad421.js', '616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc'],
  [275799, '1147ad0a1bf513f9.js', '65ec0d9fa441ca4402f8e85491e5f26fb5e0a96ac65f2493fb7e4a2e1e659523'],
  [78436, '256f83f9b5d323e6.js', '3293e7177943dd9290ef8ed4c9c65f0174fdfd8d4c7310fe0ad735b239f5e347'],
  [29542, 'fd402d4185b44ce9.js', 'ede316c07dd8ceb3faff4f840fefbb61a5b1a18d372e600225db0f8410a661bd'],
  [445242, '01ad4f413e529b60.js', '2d7f3e592645b5e2d997e444ee9b10be6dc8c357680552dccddafb63e4887576'],
  [732486, 'e01139c6299580b1.js', '1327928dc08f8c5ad213c67d8b2b042e579ca141db8b23ac448bf178077cfadd'],
];
const one = (scope, test, label) => exactlyOne(findNodes(scope, test), label);
const printed = (node) => generate(node, { comments: false }).code;
const cite = (source, node, label, text = true) => ({ ...source.witness(node, label), astType: node.type, ...(text ? { text: source.text(node) } : {}) });
function declarations(f) { return f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [n]); }
function declaration(f, key) { return exactlyOne(declarations(f).filter((n) => n.id?.name === key), `declaration ${key}`); }
function exported(f, key) {
  const values = [];
  for (const statement of f.node.body.body) {
    const n = statement.expression;
    if (n?.type !== 'CallExpression' || n.callee.object?.name !== f.runtime || propertyName(n.callee.property) !== 's') continue;
    if (n.arguments[1] && n.arguments[1].value !== f.provenance.id) continue;
    const a = n.arguments[0].elements;
    for (let i = 0; i < a.length; i += 3) if (a[i]?.value === key) values.push(a[i + 2]);
  }
  return exactlyOne(values, `export ${key}`);
}
function resolve(f, node) { return node.type === 'Identifier' ? declaration(f, node.name).init ?? declaration(f, node.name) : node; }
function importOf(f, id) { return exactlyOne(declarations(f).filter((n) => n.init?.type === 'CallExpression' &&
  n.init.callee.object?.name === f.runtime && n.init.arguments[0]?.value === id), `import ${id}`); }

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root), sources = [];
  for (const [id, name, hash] of EXPECTED) {
    const f = await corpus.factory(id, { source: `evidence/web/objects/${name}` });
    assert.equal(f.provenance.sha256, hash, `review changed ${id}/${name}`);
    assert.deepEqual(corpus.index.modules.filter((m) => m.ids.includes(id)).map((m) => m.sha256), [hash], `all current ${id} variants explicit`);
    sources.push(f);
  }
  const [f, quote, provider, labels, compiler, jsx] = sources;
  const C = declaration(f, 'C'), T = declaration(f, 'T'), j = declaration(f, 'j');
  const S = declaration(f, 'S'), O = declaration(f, 'O'), k = declaration(f, 'k'), A = declaration(f, 'A');
  const quoteGate = resolve(quote, exported(quote, 'Q'));
  assert.equal(quote.text(quoteGate), 't=>"stock"===t.kind||"pump"===t.kind');
  assert.equal(f.text(C).startsWith('C=(0,y.$)(e=>({creatorFeePercent:"",setCreatorFeePercent:'), true);
  const cacheCall = one(S, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    n.arguments[0]?.value === 39, 'complete 39-slot memo cache');
  const input = one(S, (n) => n.type === 'CallExpression' && n.arguments[0]?.type === 'MemberExpression' &&
    n.arguments[0].object.name === 'E' && propertyName(n.arguments[0].property) === 'f', 'actual controlled input');
  assert.equal(objectProperty(input.arguments[1], 'maxLength').value, 4);
  assert.equal(objectProperty(input.arguments[1], 'inputMode').value, 'decimal');
  const setter = one(S, (n) => n.type === 'AssignmentExpression' && n.right?.type === 'ArrowFunctionExpression' &&
    n.right.body.type === 'CallExpression' && n.right.body.callee.name === 'g', 'raw input setter callback');
  const visible = one(S, (n) => n.type === 'IfStatement' && n.consequent.type === 'ReturnStatement' &&
    n.consequent.argument?.type === 'NullLiteral', 'actual quote visibility return');
  const quoteSelection = one(S, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'O', 'actual quote snapshot selector');
  const readState = one(S, (n) => n.type === 'CallExpression' && n.callee.name === 'C', 'actual full state read');
  const validation = one(S, (n) => n.type === 'CallExpression' && n.callee.name === 'T', 'actual validation result');
  const error = one(S, (n) => n.type === 'CallExpression' && n.arguments[0]?.value === 'p' &&
    n.arguments[1]?.properties?.some((p) => propertyName(p.key) === 'id' && p.value.name === 'A'), 'actual error consumer');
  const parent = one(f.node, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'S' &&
    n.arguments[1]?.type === 'ObjectExpression' && n.arguments[1].properties.length === 0, 'actual default Create S mount');
  const laterReads = findNodes(f.node, (n) => n.type === 'CallExpression' && n.callee.name === 'C' && n.start > S.end);
  const laterT = one(f.node, (n) => n.type === 'CallExpression' && n.callee.name === 'T' && n.start > 50000, 'later pre-upload T recheck; static only');
  const projection = declaration(f, 'I');
  const projectionCalls = findNodes(f.node, (n) => n.type === 'CallExpression' && n.callee.name === 'I' &&
    n.arguments[0]?.type === 'ObjectExpression' && n.arguments[0].properties.some((p) => propertyName(p.key) === 'creatorFeePercent'));
  assert.equal(projectionCalls.length, 2);
  assert.equal(laterReads.length, 2);
  let optional = resolve(labels, exported(labels, 'f'));
  for (const key of ['CREATE_COIN_PAGE', 'SECTION', 'DETAIL', 'INPUT', 'OPTIONAL']) optional = objectProperty(optional, key);
  assert.equal(optional.value, '(Optional)');
  const imports = [78436, 275799, 445242, 732486, 398902, 630782, 200165, 745018, 29542].map((id) => importOf(f, id));
  const code = `export function createAdvancedCreatorFeeControl({ createBoundStore, useQuoteState, useTranslation, compiler, jsxRuntime, Collapsible, Input, Chevron }) {
    const y={$:createBoundStore}, v={g:useQuoteState,Q:${printed(quoteGate)}}, _={c:compiler},t=jsxRuntime,
      u={f:useTranslation},w=Collapsible,E={f:Input},a={J0:Chevron},N={f:{CREATE_COIN_PAGE:{SECTION:{DETAIL:{INPUT:{OPTIONAL:${printed(optional)}}}}}}};
    let ${[j, C, T, k, A].map(printed).join(',')};
    ${printed(S)}
    ${printed(O)}
    return { Control:S, store:C };
  }`;
  const client = '// Complete selected advanced-fee control translation; explicit local ports, never whole captured factories.\n' +
    '// Fee projection, funding, submission and all service/provider acquisition remain outside this module.\n' +
    generate(parse(code, { sourceType: 'module' }), { comments: false }).code + '\n';
  const contract = {
    schemaVersion: 1, authority: 'Archived Create source and actual consumers, parsed as inert AST; selected complete UI control with explicit synthetic ports',
    anchors: corpus.anchors, sources: sources.map((s) => s.provenance),
    implementation: { path: CLIENT, sha256: sha256(client), kind: 'Unmounted complete selected S control, not the full Create component' },
    witnesses: [...imports.map((n) => cite(f, n, 'actual used namespace import')),
      ...[j, C, T, k, A].map((n) => cite(f, n, 'complete local state/validation/ID declaration')),
      cite(f, S, 'complete S39-slot field/error/ARIA consumer'), cite(f, O, 'complete quote-state selector'),
      cite(f, cacheCall, 'actual39-slot compiler capability call'), cite(f, input, 'controlled text input, decimal input mode and maxlength4'),
      cite(f, setter.right, 'actual raw setter; no trim/number conversion'), cite(f, visible, 'actual absent-quote visibility return'),
      cite(f, quoteSelection, 'actual external snapshot selector call'), cite(f, readState, 'actual creator fee state read'),
      cite(f, validation, 'actual T validation call'), cite(f, error, 'actual conditional error text/ARIA consumer'),
      cite(f, parent, 'actual default Create advanced control mount; not mounted by this reconstruction'),
      ...laterReads.map((n) => cite(f, n, 'later parent fee-state subscription; static only')),
      cite(f, laterT, 'later submit validation recheck; static only'),
      cite(f, projection, 'later fee projection declaration; static only, never emitted'),
      ...projectionCalls.map((n) => cite(f, n, 'both fee projection consumers; static only, never called')),
      cite(quote, quoteGate, 'complete used pair-kind visibility helper'),
      cite(quote, resolve(quote, exported(quote, 'g')), 'original quote store/provider boundary; external, never emitted', false),
      cite(provider, exported(provider, '$'), 'actual bound-store API capability signature'),
      cite(provider, resolve(provider, exported(provider, 'f')), 'original React subscription provider boundary; external', false),
      cite(labels, optional, 'actual selected optional label literal'),
      cite(compiler, compiler.node, 'compiler bridge remains a supplied capability', false),
      cite(jsx, jsx.node, 'JSX runtime bridge remains a supplied capability', false)],
    behavior: {
      state: 'C initializes empty string; setter forwards raw value in a partial state update. External createBoundStore has the actual initializer=>bound-hook signature.',
      visibility: 'The actual O selector calls Q on snapshot.pair; only kind stock or pump is true. Missing pair still follows ordinary source access semantics; no repair or provider acquisition.',
      validation: 'Optional empty/falsy value passes; otherwise original decimal regex plus Number(value)>=0.01 and <=3. No trim, rounding or canonicalization in the input callback.',
      component: 'All39 compiler slots, dependencies, state/translation calls, default-open advanced section, raw callback, maxLength4/inputMode decimal, optional label, invalid error text, aria-invalid and describedby preserved.',
      lifetime: 'Store instance is shared by controls created from one runtime factory, matching the selected module boundary; each new runtime is an independent explicit host. Quote snapshots, translator and renderer/provider scheduling are external ports.',
      downstream: 'Both actual state subscriptions, two later I projection calls and submit T check are static context only. No fee projection, amount/funding, instruction, transaction, submit, upload or service implementation is emitted.'
    },
    attribution: ['1869 complete base-field validation/social/dialog callbacks remain separate; no helper or UI claim reused here.',
      'Existing SDK, media681/885 and upload1817 source boundaries are unchanged; this is no fee/math/transaction recovery credit.'],
    limits: ['Original React provider/quote store, translators, shared primitive components and active deployment are not reconstructed or acquired.',
      'No wallet, viewer/session, credentials/cookies, HTTP, signing, transaction or captured factory execution.',
      'Synthetic host primitive rendering and provider/quote snapshots cannot establish original DOM, provider timing, financial admission or mounted website parity.',
      'No native/backend compatibility, whole-Create completeness, visual parity, security clearance or feature milestone claim.']
  };
  return { client, contract };
}
export async function verify(root = APP_ROOT, supplied = {}) {
  const actual = await recover(root);
  for (const [key, relative] of [['client', CLIENT], ['contract', CONTRACT]]) {
    const expected = Buffer.from(key === 'client' ? actual.client : JSON.stringify(actual.contract, null, 2) + '\n');
    const bytes = supplied[key] ?? await readFile(path.join(root, relative));
    assert.ok(Buffer.isBuffer(bytes) && bytes.equals(expected), `${relative}: canonical source-derived bytes differ`);
  }
  return { sources: EXPECTED.length, witnesses: actual.contract.witnesses.length, compilerSlots: 39, mounted: false };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !['--write', '--check'].includes(mode)) throw Error('Usage: node app/scripts/original-create-advanced-fee.mjs --write|--check');
  if (mode === '--write') {
    const { client, contract } = await recover();
    await mkdir(path.dirname(path.join(APP_ROOT, CLIENT)), { recursive: true });
    await writeFile(path.join(APP_ROOT, CLIENT), client);
    await writeFile(path.join(APP_ROOT, CONTRACT), JSON.stringify(contract, null, 2) + '\n');
  }
  console.log(await verify());
}
