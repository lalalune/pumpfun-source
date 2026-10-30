import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, member, sha256 } from '../../scripts/original-contracts/source.mjs';
import { parseFlightRecords } from '../../scripts/settings-client-contract.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/explore-presentation';
const SOURCE = 'evidence/web/objects/ad258f9377db8376.js';
const FACTORY_SHA = '3417e48c11cff94d2efdafcfae6018010e97d1003122b734cd3e019f280a1134';
const code = (node) => generate(node, { comments: false }).code;
const runtimeCall = (node, runtime, name) => node?.type === 'CallExpression' && member(node.callee, runtime, name);

async function origin(corpus, factory) {
  const html = await corpus.capture('evidence/web/objects/501ddca30e455495');
  assert.equal(html.record.url, 'https://pump.fun/explore');
  const pushes = [...html.text.matchAll(/<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/g)]
    .map((match) => ({ match, value: JSON.parse(match[1]) }))
    .filter(({ value }) => value.length === 2 && value[0] === 1 && typeof value[1] === 'string');
  const stream = pushes.map(({ value }) => value[1]).join('');
  const records = parseFlightRecords(stream);
  assert.equal(records.get('120').value, 'HomePageContainer');
  assert.equal(records.get('121').value[0], 228998);
  assert.equal(records.get('121').value[2], '$120');
  const element = records.get('109').value;
  assert.equal(element[0], '$');
  assert.equal(element[1], '$L121');
  assert.deepEqual(Object.keys(element[3]), ['initialSearchParams', 'initialCoins']);
  const scripts = new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)]
    .map((match) => new URL(match[1], html.record.url).href));
  assert.ok(scripts.has(factory.provenance.url));
  return {
    capture: { source: html.record.path, url: html.record.url, sha256: html.record.sha256, bytes: html.record.bytes },
    pushes: pushes.map(({ match }) => html.witness({ start: match.index, end: match.index + match[0].length }, 'actual Explore Flight push')),
    decodedFlightSha256: sha256(stream), importRow: '121', exportNameRow: '120', elementRow: '109',
    exportName: 'HomePageContainer', initialPropNames: Object.keys(element[3]), initialScript: factory.provenance.url,
    limit: 'Observed MAIN /explore static context only; not a runtime-registration winner or provider/auth/native qualification.',
  };
}

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root);
  const choices = corpus.index.modules.filter((item) => item.ids.includes(228998));
  assert.equal(choices.length, 1, 'retain new owner variants explicitly before regeneration');
  assert.equal(choices[0].sha256, FACTORY_SHA);
  const factory = await corpus.factory(228998, { source: SOURCE });
  assert.equal(factory.provenance.sha256, FACTORY_SHA);
  const observed = await origin(corpus, factory);
  const top = factory.node.body.body;
  const imports = [];
  const bootstrap = [];
  const operations = [];
  const lazy = [];
  const statements = [];
  let exported;
  for (const node of top) {
    if (node.type === 'VariableDeclaration') {
      for (const declaration of node.declarations) {
        if (runtimeCall(declaration.init, factory.runtime, 'i')) {
          assert.equal(declaration.id.type, 'Identifier');
          const id = declaration.init.arguments[0].value;
          assert.ok(Number.isSafeInteger(id));
          imports.push({ id, binding: declaration.id.name,
            witness: factory.witness(declaration, `actual module namespace ${id}`),
            indexedVariants: corpus.index.modules.filter((item) => item.ids.includes(id))
              .map(({ sha256, origins }) => ({ sha256, origins })) });
        } else operations.push(factory.witness(declaration, `complete owner declaration ${declaration.id.name}`));
      }
    } else if (node.type === 'ExpressionStatement' && runtimeCall(node.expression, factory.runtime, 's')) {
      assert.equal(node.expression.arguments[1].value, 228998);
      const values = node.expression.arguments[0].elements;
      assert.equal(values.length, 3);
      assert.equal(values[0].value, 'HomePageContainer');
      assert.equal(values[1].value, 0);
      assert.equal(values[2].type, 'FunctionExpression');
      exported = values[2];
      operations.push(factory.witness(exported, 'complete HomePageContainer owner'));
      continue;
    } else if (node.type === 'ExpressionStatement' && runtimeCall(node.expression, factory.runtime, 'i')) {
      const id = node.expression.arguments[0].value;
      bootstrap.push({ id, witness: factory.witness(node, 'source-position initialized-module prerequisite') });
    } else operations.push(factory.witness(node, `complete ${node.type} ${node.id?.name ?? ''}`));
    const cloned = structuredClone(node);
    for (const call of findNodes(cloned, (child) => runtimeCall(child, factory.runtime, 'i'))) {
      call.callee = { type: 'Identifier', name: 'lookupModule' };
    }
    for (const call of findNodes(cloned, (child) => runtimeCall(child, factory.runtime, 'A'))) {
      assert.equal(call.arguments.length, 1);
      assert.equal(call.arguments[0].type, 'NumericLiteral');
      lazy.push({ id: call.arguments[0].value, witness: factory.witness(call, 'actual lazy namespace request') });
      call.callee = { type: 'Identifier', name: 'loadModule' };
    }
    statements.push(code(cloned));
  }
  assert.ok(exported);
  assert.equal(imports.length, 83);
  assert.equal(bootstrap.length, 1);
  assert.equal(bootstrap[0].id, 12692);
  assert.equal(lazy.length, 9);
  // The exported complete function has no runtime loader/import call. Reject
  // silently adding one to this separate adaptation path.
  assert.equal(findNodes(exported, (node) => runtimeCall(node, factory.runtime, 'i') || runtimeCall(node, factory.runtime, 'A')).length, 0);
  const namespaceIds = [...new Set(imports.map(({ id }) => id))];
  const required = [...namespaceIds, 12692];
  const globals = ['window', 'document', 'Date', 'setTimeout', 'clearTimeout', 'fetch', 'IntersectionObserver'];
  const text = `// Editable complete MAIN Explore owner; generated from authenticated AST.\n// Captured factories stay inert. Initialized namespaces, providers/actions and\n// resource acquisition are explicit caller-owned capabilities.\nexport const REQUIRED_MODULES = Object.freeze(${JSON.stringify(required)});\nexport const LAZY_MODULES = Object.freeze(${JSON.stringify(lazy.map(({ id }) => id))});\nexport function createExplorePresentation({modules,loadModule,host}) {\n  if (!(modules instanceof Map) || typeof loadModule !== 'function' || !host) throw new TypeError('explicit initialized source namespaces, loader and host capabilities required');\n  for (const id of REQUIRED_MODULES) if (!modules.has(id)) throw new TypeError('required initialized source namespace '+id);\n  for (const name of ${JSON.stringify(globals)}) if (!Object.hasOwn(host,name)) throw new TypeError('required actual host capability '+name);\n  const lookupModule = id => { if (!modules.has(id)) throw new TypeError('unprovided source namespace '+id); return modules.get(id); };\n  const {window,document,Date,setTimeout,clearTimeout,fetch,IntersectionObserver}=host;\n${statements.map((line) => line.split('\n').map((line) => '  ' + line).join('\n')).join('\n')}\n  const HomePageContainer = ${code(exported)};\n  return Object.freeze({HomePageContainer,PresentationFrame:ek,CoinGrid:I,AnimatedGrid:w,Pagination:ee,LinkPagination:er,pageNumbers:Q,PartialStatus:D,FeedError:H,admitLiveCoin:tl});\n}\n`;
  const proof = {
    schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors,
    origin: observed, factory: factory.provenance, imports, bootstrap, lazy, operations,
    moduleSha256: sha256(text),
    transformation: [
      'All owner top-level declarations, complete exported function, local callbacks, refs/effects/compiler caches and protected-capability handoffs are retained.',
      'Only runtime module imports and namespace loading become explicit caller-provided lookups; original bootstrap/provider/resource implementations never execute here.',
      'Global browser/timer/clock/fetch/observer interfaces are exact named host capabilities, without an ambient network fallback.',
      'Named returned local frames are authored editable access points to complete original functions, not original export-name claims.',
    ],
    credit: [
      'OPEN1867 owns379705 board query/read-state; namespace API remains required, never copied.',
      'Accepted main search-session493025 normalization remains unchanged and required through original namespace API.',
      'Accepted695 request attribution, OPEN1761 response and existing settings/bookmarks/provider/card/Avatar/chart presentation packages retain attribution; none copied.',
      'OPEN1937/1925/1962 shared SearchDialog frames are distinct from this actual228998 MAIN owner.',
    ],
    limits: {
      capturedExecution: false, activeRegistrationWinner: false, providerImplementation: false,
      actualNetwork: false, credentialSessionAcquisition: false, protectedActions: false,
      deferredPerpsImplementation: false, originalAnimationLibrary: false, originalLazyLoader: false,
      mountedApp: false, originalCSSVisualParity: false, financialNativeCompatibility: false,
      featureCompletion: false, securityAcceptance: false,
    },
  };
  return { text, proof };
}

export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  assert.equal(await readFile(path.join(root, DIRECTORY, 'client.mjs'), 'utf8'), result.text, 'complete Explore owner source differs');
  assert.deepEqual(JSON.parse(await readFile(path.join(root, DIRECTORY, 'PROVENANCE.json'), 'utf8')), result.proof, 'Explore provenance differs');
  return result.proof;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv[2] === '--write') {
    const result = await recover();
    await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true });
    await writeFile(path.join(APP_ROOT, DIRECTORY, 'client.mjs'), result.text);
    await writeFile(path.join(APP_ROOT, DIRECTORY, 'PROVENANCE.json'), JSON.stringify(result.proof, null, 2) + '\n');
  } else { assert.equal(process.argv[2], '--check'); await verify(); }
  console.log('Complete MAIN Explore presentation source PASS');
}
