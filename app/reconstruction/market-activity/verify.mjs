import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import prettier from 'prettier';
import { openCorpus, findNodes, exactlyOne, member, sha256 } from '../../scripts/original-contracts/source.mjs';
import { normalizeSession } from '../../scripts/verify-search-session.mjs';

export const APP_ROOT = fileURLToPath(new URL('../..', import.meta.url));
export const DIRECTORY = 'reconstruction/market-activity';
const COUNTS = new Map([[849812, 4], [680930, 6], [26077, 1], [975982, 1],
  [605587, 1], [503630, 1], [796654, 1], [457065, 1]]);
const HOOK_HASHES = ['8e943b080637dd380ecbd1632becbead8b3bed4782676c99c2a43268f6e538de',
  '3b8b0b598d7596ed60742816b9731945e42f3845d9a5b27b8b12449a363efd4a',
  '49ebaebccb417a673e9b591596ee99e7bf85e0ba663a70cf16f32a05cd13c6e5',
  'e3bb5a0382fedc4d9624aa44772bc998442b8c6b5b519e77a3c21bcf8eee246d'];
const entries = (f) => f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration'
  ? n.declarations : n.type === 'FunctionDeclaration' ? [n] : []);
const resolve = (f, n) => n.type === 'Identifier' ? (() => {
  const d = exactlyOne(entries(f).filter((d) => d.id.name === n.name), 'actual binding ' + n.name);
  return d.init ?? d;
})() : n;
function exported(f, name) {
  const call = exactlyOne(findNodes(f.node, (n) => n.type === 'CallExpression' &&
    member(n.callee, f.runtime, 's') && n.arguments[0]?.type === 'ArrayExpression' &&
    n.arguments[0].elements.some((x) => x?.value === name)), 'actual export ' + f.id + '.' + name);
  assert.ok(!call.arguments[1] || call.arguments[1].value === f.id);
  const a = call.arguments[0].elements, at = a.findIndex((x) => x?.value === name);
  assert.equal(a[at + 1].value, 0);
  return resolve(f, a[at + 2]);
}
function imports(f) {
  return new Map(entries(f).filter((d) => d.init?.type === 'CallExpression' &&
    member(d.init.callee, f.runtime, 'i')).map((d) => [d.init.arguments[0].value, d]));
}
const globals = Object.fromEntries(['Array', 'Set', 'Object', 'Boolean', 'Number', 'JSON', 'Error']
  .map((n) => [n, 'global:' + n]));
function context(f) {
  const qualified = {};
  for (const [id, declaration] of imports(f)) for (const prop of {
    445242: ['c'], 254667: ['y'], 975982: ['k'], 132838: ['f'], 935258: ['f'],
    606933: ['useQueryClient'], 796654: ['f'], 503630: ['V'], 605587: ['h'],
    26077: ['f'], 680930: ['t', '$', 'd'],
  }[id] ?? []) qualified[declaration.id.name + '.' + prop] = 'operation:' + id + '.' + prop;
  const roles = { ...globals };
  for (const name of ['g', 'l']) {
    const fn = exported(f, name);
    if (fn.id) roles[fn.id.name] = 'local-export:' + name;
    else {
      const d = exactlyOne(entries(f).filter((d) => d.init === fn), 'predicate declaration');
      roles[d.id.name] = 'local-export:' + name;
    }
  }
  const combiner = exactlyOne(f.node.body.body.filter((n) => n.type === 'FunctionDeclaration' &&
    n !== exported(f, 'g') && findNodes(n, (x) => x.type === 'ObjectProperty' && x.key.name === 'pending').length), 'actual combine');
  roles[combiner.id.name] = 'local:combine';
  const selectors = f.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n !== exported(f, 'g') && n !== combiner);
  assert.equal(selectors.length, 3);
  for (const fn of selectors) {
    assert.equal(fn.body.body.length, 1);
    const result = fn.body.body[0].argument;
    assert.equal(result.type, 'MemberExpression');
    roles[fn.id.name] = 'local:select:' + result.property.name;
  }
  return { roles, qualified, combiner, selectors };
}

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root), factories = [], selected = new Map(), witnesses = [], comparisons = [];
  for (const [id, count] of COUNTS) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id));
    assert.equal(variants.length, count, 'all physical variants required for ' + id);
    if (id === 849812) assert.deepEqual(variants.map((v) => v.sha256).sort(), [...HOOK_HASHES].sort());
    const found = [];
    for (const v of variants) for (const origin of v.origins) {
      const f = await corpus.factory(id, { source: origin.source });
      assert.equal(f.provenance.sha256, v.sha256);
      factories.push(f.provenance); found.push(f);
    }
    selected.set(id, found);
  }
  const one = (id) => exactlyOne(selected.get(id), 'unique physical ' + id);
  const cite = (f, n, label) => {
    const w = f.witness(n, label); witnesses.push(w); return w;
  };
  const compare = (f, n, expected, label, roles = {}, qualified = {}) => {
    const value = normalizeSession(n, { ...globals, ...roles }, qualified);
    assert.deepEqual(value, expected, 'complete source operation differs: ' + label);
    comparisons.push({ ...cite(f, n, label), normalizedSha256: sha256(JSON.stringify(value)) });
  };
  const hooks = selected.get(849812), canonical = hooks[0], canonicalContext = context(canonical);
  const frames = [];
  for (const f of hooks) {
    const ctx = context(f), hook = exported(f, 'b');
    const helper = await corpus.factory(680930, { source: f.provenance.source });
    assert.ok(selected.get(680930).some((p) => p.provenance.sha256 === helper.provenance.sha256));
    for (const [label, node, expected] of [
      ['complete 31-slot owning query frame', hook, exported(canonical, 'b')],
      ['complete POST reader/catch/normalization', exported(f, 'g'), exported(canonical, 'g')],
      ['complete address admission predicate', exported(f, 'l'), exported(canonical, 'l')],
      ['complete combined query projection', ctx.combiner, canonicalContext.combiner],
    ]) compare(f, node, normalizeSession(expected, canonicalContext.roles, canonicalContext.qualified), label, ctx.roles, ctx.qualified);
    for (const fn of ctx.selectors) {
      const role = ctx.roles[fn.id.name], expected = exactlyOne(canonicalContext.selectors.filter((n) => canonicalContext.roles[n.id.name] === role), 'canonical selector');
      compare(f, fn, normalizeSession(expected, canonicalContext.roles, canonicalContext.qualified), 'complete ' + role, ctx.roles, ctx.qualified);
    }
    const allocation = exactlyOne(findNodes(hook, (n) => n.type === 'CallExpression' && n.arguments[0]?.value === 31), 'actual memo allocation');
    assert.ok(allocation.callee.type === 'SequenceExpression');
    frames.push({ factory: f.provenance, frame: f.witness(hook, 'complete original owning hook'), helperFactory: helper.provenance });
    for (const [id, n] of imports(f)) cite(f, n, 'actual dependency import ' + id);
  }
  const batch = exactlyOne(selected.get(680930).filter((f) => f.provenance.source === canonical.provenance.source), 'canonical same-source batching');
  const config = exported(batch, 't'), configName = exactlyOne(entries(batch).filter((d) => d.init === config), 'config binding').id.name;
  for (const f of selected.get(680930)) {
    const cfg = exported(f, 't'), name = exactlyOne(entries(f).filter((d) => d.init === cfg), 'config binding').id.name;
    compare(f, cfg, normalizeSession(config, globals), 'complete used query/batch configuration');
    for (const name of ['$', 'd']) compare(f, exported(f, name),
      normalizeSession(exported(batch, name), { ...globals, [configName]: 'module:config' }),
      'complete used helper ' + name, { [exactlyOne(entries(f).filter((d) => d.init === cfg), 'config declaration').id.name]: 'module:config' });
  }
  const normalizer = one(26077), solana = one(975982), evm = one(605587), origin = one(503630), transport = one(796654), parent = one(457065);
  const volumeFields = exactlyOne(entries(normalizer).filter((d) => d.init?.type === 'ArrayExpression'), 'volume fields');
  const normalizerHelpers = normalizer.node.body.body.filter((n) => n.type === 'FunctionDeclaration');
  assert.equal(normalizerHelpers.length, 3);
  cite(normalizer, volumeFields, 'actual normalized volume fields');
  normalizerHelpers.forEach((n) => cite(normalizer, n, 'complete used normalization dependency'));
  cite(normalizer, exported(normalizer, 'f'), 'complete record/window response normalization');
  const solanaPattern = exactlyOne(entries(solana).filter((d) => d.init?.type === 'RegExpLiteral'), 'base58 alphabet');
  cite(solana, solanaPattern, 'actual Solana alphabet');
  cite(solana, exported(solana, 'k'), 'complete trimmed-test/noncanonicalized-output Solana predicate');
  cite(evm, exported(evm, 'h'), 'complete strict EVM address predicate');
  cite(origin, exported(origin, 'V'), 'credited origin selector only; never an implicit destination');
  cite(transport, exported(transport, 'f'), 'external fetch/telemetry wrapper; not implemented');
  const parentImport = imports(parent).get(849812);
  assert.ok(parentImport);
  cite(parent, parentImport, 'actual Mayhem activity-hook import');
  const parentCall = exactlyOne(findNodes(parent.node, (n) => n.type === 'CallExpression' &&
    n.callee.type === 'SequenceExpression' && member(n.callee.expressions.at(-1), parentImport.id.name, 'b')), 'actual Mayhem hook call');
  assert.equal(parentCall.arguments.length, 1);
  cite(parent, parentCall, 'actual one-argument Mayhem activity handoff');
  cite(parent, exactlyOne(findNodes(parent.node, (n) => n.type === 'AssignmentExpression' &&
    n.right.type === 'CallExpression' && member(n.right.callee, 'eK', 'map')), 'actual base-coin mint projection'), 'base query coins become activity mint input');
  cite(parent, exactlyOne(parent.node.body.body.filter((n) => n.type === 'FunctionDeclaration' && n.id.name === 'ee'), 'mint selector'), 'actual mint selector');
  const portFields = { 445242: ['c', 'useMemoCache'], 254667: ['y', 'logger'], 975982: ['k', 'isSolanaActivityAddress'],
    132838: ['f', 'useMutation'], 935258: ['f', 'useQueries'], 606933: ['useQueryClient', 'useQueryClient'],
    796654: ['f', 'fetchActivity'], 503630: ['V', 'getBaseUrl'], 605587: ['h', 'isEvmActivityAddress'],
    26077: ['f', 'normalizeMarketActivity'] };
  const namespaceBindings = [...imports(canonical)].map(([id, d]) => {
    if (id === 680930) return `${d.id.name}={t:ACTIVITY_CONFIG,$:splitActivityBatches,d:mergeActivityBatches}`;
    assert.ok(portFields[id], 'unclosed hook import ' + id);
    const [prop, value] = portFields[id]; return `${d.id.name}={${prop}:${value}}`;
  }).join(',');
  const predicateBinding = exactlyOne(entries(canonical).filter((d) => d.init === exported(canonical, 'l')), 'canonical predicate binding');
  const originalFunctions = canonical.node.body.body.filter((n) => n.type === 'FunctionDeclaration');
  const text = await prettier.format(`
// Source-bound editable activity operations. No implicit destination or provider.
export const ACTIVITY_CONFIG=${batch.text(config)};
export const isSolanaActivityAddress=(()=>{let ${solana.text(solanaPattern)};return ${solana.text(exported(solana, 'k'))};})();
export const isEvmActivityAddress=${evm.text(exported(evm, 'h'))};
export const normalizeMarketActivity=(()=>{let ${normalizer.text(volumeFields)};${normalizerHelpers.map((n) => normalizer.text(n)).join('\n')}return ${normalizer.text(exported(normalizer, 'f'))};})();
const batchOperations=(()=>{const ${configName}=ACTIVITY_CONFIG;return {split:${batch.text(exported(batch, '$'))},merge:${batch.text(exported(batch, 'd'))}};})();
export const splitActivityBatches=batchOperations.split;
export const mergeActivityBatches=batchOperations.merge;
export function createMarketActivityModule({getBaseUrl,fetchActivity,logger,useMemoCache,useQueryClient,useQueries,useMutation}){
 for(const [name,value]of Object.entries({getBaseUrl,fetchActivity,useMemoCache,useQueryClient,useQueries,useMutation}))if(typeof value!=='function')throw new TypeError('Explicit activity capability required: '+name);
 if(typeof logger?.warn!=='function')throw new TypeError('Explicit activity logger.warn required');
 const ${namespaceBindings};
 let ${canonical.text(predicateBinding)};
 ${originalFunctions.map((n) => canonical.text(n)).join('\n')}
 return {isActivityAddress:${predicateBinding.id.name},readMarketActivity:${exported(canonical, 'g').id.name},useMarketActivity:${canonical.text(exported(canonical, 'b'))}};
}
`, { parser: 'babel' });
  return { text, provenance: { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a',
    scope: 'Complete used market-activity reader/query frame with explicit provider capabilities; no service or mounted/native feature',
    anchors: corpus.anchors, factories, frames, comparisons, witnesses,
    moduleSha256: sha256(Buffer.from(text)), ports: { getBaseUrl: 'Actual503630.V invocation, explicit host return; no automatic network origin',
      fetchActivity: 'Actual796654.f fetch + telemetry dependency; wrapper telemetry/store/classifier/provider not recovered',
      logger: 'Actual254667.y.warn capability; no logger/storage/server implementation',
      query: 'Actual445242.c(31),606933.useQueryClient,935258.f(useQueries),132838.f(useMutation) capabilities; query library internals external' },
    credit: ['Existing503630 origin attribution', '1812 parent/view-data consumer is witnessed, not copied or newly credited'],
    limits: ['Original captured factories are parsed inertly, never evaluated/imported',
      'Only used680930 t/$/d and26077 f closure; unrelated metrics/storage/provider exports excluded',
      'No auth/device/session acquisition, telemetry, market service/socket/cache implementation, financial/native/API/browser/UI qualification or coverage change'] } };
}
export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  assert.equal(await readFile(path.join(root, DIRECTORY, 'client.mjs'), 'utf8'), result.text, 'activity module differs from source adaptation');
  assert.equal(await readFile(path.join(root, DIRECTORY, 'PROVENANCE.json'), 'utf8'), JSON.stringify(result.provenance, null, 2) + '\n', 'activity provenance differs');
  return result.provenance;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  assert.ok(process.argv.length === 3 && ['--write', '--check'].includes(process.argv[2]), 'Use --write|--check');
  if (process.argv[2] === '--write') {
    const r = await recover(); await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP_ROOT, DIRECTORY, 'client.mjs'), r.text);
    await writeFile(path.join(APP_ROOT, DIRECTORY, 'PROVENANCE.json'), JSON.stringify(r.provenance, null, 2) + '\n');
  } else await verify();
  console.log('PASS complete market-activity frame/reader/helpers and all physical variants');
}
