import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import prettier from 'prettier';
import { openCorpus, findNodes, member, exactlyOne, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const DIRECTORY = 'reconstruction/creator-payout-client';
const SHARED = 'a7c04fdc74fb88a27d5cf24355396ee560d88ad4042abf3eb6a3c6874c5bacf2';
const VARIANTS = [
  ['evidence/web/objects/57cc59637a8b8f78.js', '50adeb832d22cb5cb8df1dba280ff38966dbb85f2730d94a872aedd60c2234c5'],
  ['evidence/web/objects/dd1b7e2a0ecbaed0.js', 'ff013c07164d5f58aed101e8221f512ced1c7d39fce2896fedf6bfa548d0a99f'],
  ['evidence/web/objects/bbad3cca63bc2aa5.js', 'd99e0ef0c84649f4f27ccdcd238cd183c60bfec152054a0bcce59d0945aef520'],
];
const CAPABILITIES = {
  445242: ['c', 'useMemoCache'], 761459: ['useInfiniteQuery', 'useInfiniteQuery'],
  690877: ['useQuery', 'useQuery'], 759257: ['j', 'createClient'],
};
const EXPORTS = {
  '493270.j': 'FetchError', '493270.y': 'requestLeaderboard',
  '493270.n': 'requestOwnTotal', '493270.X': 'nextPage', '493270.z': 'rowKey',
  '80559.a': 'useLeaderboard', '80559.U': 'useOwnTotal',
};
const CONSUMERS = [
  [66397, 'evidence/web/objects/dd1b7e2a0ecbaed0.js', '04f336660c3e57d49f82f4e857a9d8a64aba011116b87d437ad8c16ac7128e3b'],
  [66397, 'evidence/web/objects/bbad3cca63bc2aa5.js', '43e295eb30627cb4a9c249be3e6103592c114b2d4daec8beaca191e1753b9877'],
  [590407, 'evidence/web/objects/2fe17dced92b840b.js', '3f494070c58a6d7f0f70279887ef648107935b765fe849de3e9ec100cec45dda'],
];
const tail = (node) => node.type === 'SequenceExpression' ? node.expressions.at(-1) : node;

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== 'object') return value;
  return Object.fromEntries(Object.entries(value).filter(([key]) => ![
    'start', 'end', 'loc', 'extra', 'comments', 'leadingComments', 'trailingComments', 'innerComments',
  ].includes(key)).map(([key, item]) => [key, canonical(item)]));
}

async function physical(corpus, id, source, hash) {
  const factory = await corpus.factory(id, { source });
  assert.equal(factory.provenance.sha256, hash, `unreviewed source ${id}`);
  assert.equal(factory.capture.factories.filter((entry) => entry.ids.includes(id)).length, 1);
  return factory;
}

function exportsOf(factory) {
  const exports = new Map();
  const statements = [];
  for (const statement of factory.node.body.body) {
    const call = statement.type === 'ExpressionStatement' ? statement.expression : null;
    if (call?.type !== 'CallExpression' || !member(call.callee, factory.runtime, 's')) continue;
    assert.equal(call.arguments[0].type, 'ArrayExpression');
    const id = call.arguments[1].value;
    assert.ok(factory.ids.includes(id));
    const entries = call.arguments[0].elements;
    assert.equal(entries.length % 3, 0);
    for (let index = 0; index < entries.length; index += 3) {
      assert.equal(entries[index].type, 'StringLiteral');
      assert.equal(entries[index + 1].value, 0);
      const key = `${id}.${entries[index].value}`;
      assert.ok(!exports.has(key));
      exports.set(key, entries[index + 2]);
    }
    statements.push(statement);
  }
  assert.deepEqual([...exports.keys()].sort(), Object.keys(EXPORTS).sort());
  assert.equal(statements.length, 2);
  return { exports, statements };
}

function sourceExport(factory, id, name) {
  const found = [];
  for (const call of findNodes(factory.node, (node) => node.type === 'CallExpression' && member(node.callee, factory.runtime, 's') &&
    (node.arguments[1]?.value === id || (!node.arguments[1] && factory.ids.length === 1 && factory.id === id)))) {
    const entries = call.arguments[0].elements;
    for (let index = 0; index < entries.length; index += 3) {
      if (entries[index].value === name) found.push(entries[index + 2]);
    }
  }
  return exactlyOne(found, `actual export ${id}.${name}`);
}

export async function buildCreatorPayoutClient(appRoot = APP_ROOT) {
  assert.equal(sha256(await readFile(path.join(appRoot, 'scripts/original-contracts/source.mjs'))), SHARED);
  const corpus = await openCorpus(appRoot);
  for (const id of [80559, 493270]) {
    assert.deepEqual(corpus.index.modules.filter((row) => row.ids.includes(id)).map((row) => row.sha256).sort(),
      VARIANTS.map(([, hash]) => hash).sort(), `unreviewed complete variant set ${id}`);
  }
  const outputs = new Map();
  const variants = [];
  const witnesses = [];
  for (const [source, hash] of VARIANTS) {
    const factory = await physical(corpus, 80559, source, hash);
    assert.deepEqual(factory.ids, [80559, 493270]);
    const imports = factory.node.body.body[0];
    assert.equal(imports.type, 'VariableDeclaration');
    assert.equal(imports.kind, 'var');
    assert.equal(imports.declarations.length, 4);
    const replacements = [];
    const imported = [];
    for (const declaration of imports.declarations) {
      assert.ok(member(declaration.init.callee, factory.runtime, 'i'));
      const id = declaration.init.arguments[0].value;
      assert.ok(CAPABILITIES[id]);
      const [property, capability] = CAPABILITIES[id];
      replacements.push(`${declaration.id.name}={${JSON.stringify(property)}:${capability}}`);
      imported.push(id);
      witnesses.push(factory.witness(declaration, `${hash.slice(0, 12)} actual import ${id}`));
    }
    assert.deepEqual(imported.sort((a, b) => a - b), Object.keys(CAPABILITIES).map(Number).sort((a, b) => a - b));
    const { exports, statements } = exportsOf(factory);
    const retained = factory.node.body.body.filter((node) => node !== imports && !statements.includes(node));
    assert.ok(retained.every((node) => ['FunctionDeclaration', 'ClassDeclaration', 'VariableDeclaration'].includes(node.type)));
    const publicValues = Object.entries(EXPORTS).map(([key, name]) => `${name}:${factory.text(exports.get(key))}`).join(',');
    const text = await prettier.format(`// Maintained source adaptation: one explicit original module instance; no original runtime execution.\nexport function createModule({useMemoCache,useInfiniteQuery,useQuery,createClient}){var ${replacements.join(',')};\n${retained.map((node) => factory.text(node)).join('\n')}\nreturn {${publicValues}};}`, { parser: 'babel' });
    const filename = `variants/${hash.slice(0, 12)}.mjs`;
    outputs.set(filename, text);
    const nodes = [...retained, ...[...exports.values()].filter((node) => node.type === 'FunctionExpression')];
    for (const node of nodes) witnesses.push(factory.witness(node, `${hash.slice(0, 12)} retained complete ${node.type}`));
    variants.push({ factory: factory.provenance, path: filename, adapterSha256: sha256(text),
      retainedAsts: nodes.map((node) => ({ type: node.type, sha256: sha256(JSON.stringify(canonical(node))) })) });
  }
  const consumers = [];
  for (const [id, source, hash] of CONSUMERS) {
    const factory = await physical(corpus, id, source, hash);
    const binding = new Map();
    for (const node of findNodes(factory.node, (node) => node.type === 'VariableDeclarator' &&
      node.init?.type === 'CallExpression' && member(node.init.callee, factory.runtime, 'i') &&
      [80559, 493270].includes(node.init.arguments[0]?.value))) {
      binding.set(node.init.arguments[0].value, node.id.name);
      witnesses.push(factory.witness(node, `actual consumer ${id} import ${node.init.arguments[0].value}`));
    }
    for (const [moduleId, name] of [[80559, 'a'], [80559, 'U'], [493270, 'z']]) {
      const calls = findNodes(factory.node, (node) => node.type === 'CallExpression' && member(tail(node.callee), binding.get(moduleId), name));
      assert.ok(calls.length, `missing actual consumer ${id}: ${moduleId}.${name}`);
      for (const call of calls) witnesses.push(factory.witness(call, `actual consumer ${id}: ${moduleId}.${name}`));
    }
    consumers.push(factory.provenance);
  }
  const transport = await physical(corpus, 759257, 'evidence/web/objects/1e479323ffe53c14.js', 'e1c207697339004b48f6baa9f81f34e7644686ee424616b553e55b23c659b855');
  const origin = await physical(corpus, 503630, 'evidence/web/objects/1e479323ffe53c14.js', 'df5a12d4b76158889dd38a02d0d9afc0d0405065772b589c9cadf9806422d0e7');
  const usedClient = sourceExport(transport, 759257, 'j');
  const base = sourceExport(origin, 503630, 'R');
  assert.equal(base.body.type, 'StringLiteral');
  const originImport = exactlyOne(findNodes(transport.node, (node) => node.type === 'VariableDeclarator' &&
    node.init?.type === 'CallExpression' && member(node.init.callee, transport.runtime, 'i') && node.init.arguments[0]?.value === 503630), 'client origin import');
  assert.equal(findNodes(usedClient, (node) => node.type === 'CallExpression' && member(tail(node.callee), originImport.id.name, 'R')).length, 1);
  witnesses.push(transport.witness(usedClient, 'actual used 759257.j contract-client factory'), origin.witness(base, 'actual 503630.R origin configuration'));
  const declaration = await physical(corpus, 190491, 'evidence/web/objects/2b47dd0b38a1608f.js', '36fb23be0c2cded3fa8b2c242b0ebf06a594381c34236e2341fa6408e635118d');
  for (const operation of ['GET /payouts/leaderboard', 'GET /payouts']) {
    const property = exactlyOne(findNodes(declaration.node, (node) => node.type === 'ObjectProperty' && node.key?.type === 'StringLiteral' && node.key.value === operation), operation);
    witnesses.push(declaration.witness(property, `separate declared schema ${operation}; not executed`));
  }
  const imports = variants.map((row, index) => `import {createModule as v${index}} from './${row.path}';`).join('\n');
  const table = variants.map((row, index) => `[${JSON.stringify(row.factory.sha256)},v${index}]`).join(',');
  outputs.set('client.mjs', await prettier.format(`${imports}\nconst factories=new Map([${table}]);\nexport const creatorPayoutVariants=Object.freeze(${JSON.stringify(variants.map((row) => ({ sha256: row.factory.sha256, source: row.factory.source })))}.map(Object.freeze));\nexport function createCreatorPayoutModule({variant,...capabilities}){const factory=factories.get(variant);if(!factory)throw new TypeError('Explicit reviewed creator-payout source variant required');return factory(capabilities);}`, { parser: 'babel' }));
  const ids = [80559, 493270, 66397, 590407, 759257, 503630, 190491];
  const selected = corpus.index.modules.filter((row) => row.ids.some((id) => ids.includes(id))).sort((a, b) => a.sha256.localeCompare(b.sha256));
  const contract = {
    schemaVersion: 1, source: { reviewBase: '49d07973846893ac42df69ef9008a54b17f5b5bd', manifestSha256: corpus.anchors.manifestSha256,
      selectedIndexEntries: selected, selectedCompleteEntriesSha256: sha256(JSON.stringify(selected)), sharedSourceSha256: SHARED },
    scope: 'Complete original creator-payout frontend module instances: row normalization, read requests, infinite paging and typed error/query policies; no server payout or ranking implementation.',
    explicitVariantSelection: 'Required full original factory SHA; no default or deployment-active winner claim.',
    variants, consumers, dependencies: [transport.provenance, origin.provenance, declaration.provenance],
    capabilities: CAPABILITIES, originalExports: EXPORTS,
    witnesses: witnesses.sort((a, b) => a.source.localeCompare(b.source) || a.utf16[0] - b.utf16[0]),
    behavior: { leaderboardOperation: 'GET /payouts/leaderboard', ownTotalOperation: 'GET /payouts', capturedWebsiteOrigin: base.body.value, pageSize: 50,
      allPeriod: 'Request omits period only for literal all; the original parameter default applies only to undefined.',
      pagination: 'Stop when normalized last-page entries length <50 or loaded entries >=min(500,lastPage.totalEarners); otherwise lastPageParam+1.',
      normalization: 'Original finite-number/string/boolean guards and entry whitelist retained; no sorting, aggregation or guessed response fields.',
      unauthorized: 'Only the module instance FetchError with status401 disables leaderboard retry/window-focus/refetch interval.',
      providerBoundary: 'React memo and query scheduling plus contract HTTP/auth remain explicit injected capabilities; own-total wallet key is not server authorization.' },
    limits: ['Original captures and route schemas are parsed, never evaluated.', 'Each API construction represents one original module instance with its own original error constructor.',
      'No real cookies, credentials, personal payouts or production APIs are used.', 'No frontend route/style, server auth, payout calculation, private backend or full API/visual compatibility claim.'],
  };
  return { outputs, contract };
}

export async function verifyCreatorPayoutClient(appRoot = APP_ROOT) {
  const { outputs, contract } = await buildCreatorPayoutClient(appRoot);
  for (const [name, expected] of outputs) {
    const actual = await readFile(path.join(appRoot, DIRECTORY, name), 'utf8');
    assert.deepEqual(canonical(parse(actual, { sourceType: 'module' })), canonical(parse(expected, { sourceType: 'module' })), `maintained AST differs: ${name}`);
    assert.equal(actual, expected, `maintained canonical bytes differ: ${name}`);
  }
  assert.equal(await readFile(path.join(appRoot, DIRECTORY, 'contract.json'), 'utf8'), JSON.stringify(contract, null, 2) + '\n', 'source contract differs');
  return contract;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const [mode, ...rest] = process.argv.slice(2);
    assert.ok(!rest.length && ['--write', '--check'].includes(mode), 'usage: --write | --check');
    if (mode === '--write') {
      const { outputs, contract } = await buildCreatorPayoutClient();
      for (const [name, text] of outputs) { const file = path.join(APP_ROOT, DIRECTORY, name); await mkdir(path.dirname(file), { recursive: true }); await writeFile(file, text); }
      await writeFile(path.join(APP_ROOT, DIRECTORY, 'contract.json'), JSON.stringify(contract, null, 2) + '\n');
    } else await verifyCreatorPayoutClient();
    console.log('Original creator-payout modules verified without captured runtime execution.');
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
