import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, member, sha256 } from '../../scripts/original-contracts/source.mjs';
import { parseFlightRecords } from '../../scripts/settings-client-contract.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/explore-coin-card';
const PINS = [
  ['bfec4df69fcd3f968311aa991fac862a02712595c4d38b60b07e74fd7f48a7a2', 'evidence/web/objects/bf334c55745d2868.js', { media: 'b', bookmark: 'S', charity: 'R', live: 'T', mayhem: 'A', creator: 'D', subscribe: 'ea', snapshot: 'en', server: 'es' }],
  ['635d9d462036785668cd1805d8ace0515fa5d01b4744828a3193f9002af7c0dd', 'evidence/web/objects/ee92e9e880aedbf0.js', { media: 'v', bookmark: 'M', charity: 'R', live: 'D', mayhem: 'T', creator: 'L', subscribe: 'ei', snapshot: 'en', server: 'el' }],
];
const code = (node) => generate(node, { comments: false }).code;
const call = (node, runtime, name) => node?.type === 'CallExpression' && member(node.callee, runtime, name);

async function incoming(corpus, cards) {
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
  assert.equal(records.get('109').value[1], '$L121');
  const scripts = new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map((match) => new URL(match[1], html.record.url).href));
  const parent = await corpus.factory(228998, { source: 'evidence/web/objects/ad258f9377db8376.js' });
  assert.equal(parent.provenance.sha256, '3417e48c11cff94d2efdafcfae6018010e97d1003122b734cd3e019f280a1134');
  assert.ok(scripts.has(parent.provenance.url));
  const grid = exactlyOne(parent.node.body.body.flatMap((node) => node.type === 'VariableDeclaration' ? node.declarations : [])
    .filter((node) => node.id.name === 'I'), 'actual complete83memo grid');
  const imported = exactlyOne(parent.node.body.body.flatMap((node) => node.type === 'VariableDeclaration' ? node.declarations : [])
    .filter((node) => call(node.init, parent.runtime, 'i') && node.init.arguments[0].value === 871999), 'actual Card namespace binding');
  const edge = exactlyOne(findNodes(grid, (node) => node.type === 'CallExpression' &&
    member(node.callee, 't', 'jsx') && member(node.arguments[0], imported.id.name, 'f')), 'actual grid Card props');
  assert.equal(edge.arguments[1].type, 'ObjectExpression');
  const initial = cards.map((factory) => ({ ...factory.provenance, initialScript: scripts.has(factory.provenance.url) }));
  assert.equal(initial.filter(({ initialScript }) => initialScript).length, 1);
  return {
    capture: { source: html.record.path, url: html.record.url, sha256: html.record.sha256, bytes: html.record.bytes },
    pushes: pushes.map(({ match }) => html.witness({ start: match.index, end: match.index + match[0].length }, 'actual Explore Flight context')),
    decodedFlightSha256: sha256(stream), importRow: '121', nameRow: '120', elementRow: '109',
    parent: parent.provenance, import: parent.witness(imported, 'actual871999 namespace import'),
    grid: parent.witness(grid, 'complete actual83memo owning grid'), props: parent.witness(edge, 'complete actual Card prop handoff'),
    cardContexts: initial,
    limit: 'Observed MAIN /explore initial/static caller only; alternative contexts retained, no global active-registration winner or individual-token route qualification.',
  };
}

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root);
  assert.deepEqual(corpus.index.modules.filter((item) => item.ids.includes(871999)).map(({ sha256 }) => sha256), PINS.map(([sha]) => sha));
  const factories = [];
  const builders = [];
  const contexts = [];
  for (const [pin, source, names] of PINS) {
    const factory = await corpus.factory(871999, { source });
    assert.equal(factory.provenance.sha256, pin);
    factories.push(factory);
    const imports = [], operations = [], prerequisites = [], lazy = [], statements = [];
    let exported;
    for (const node of factory.node.body.body) {
      if (node.type === 'VariableDeclaration') {
        for (const declaration of node.declarations) {
          if (call(declaration.init, factory.runtime, 'i')) imports.push({ id: declaration.init.arguments[0].value, binding: declaration.id.name, witness: factory.witness(declaration, 'actual required namespace') });
          else operations.push(factory.witness(declaration, `complete local ${declaration.id.name}`));
        }
      } else if (node.type === 'ExpressionStatement' && call(node.expression, factory.runtime, 's')) {
        assert.equal(node.expression.arguments[1].value, 871999);
        const values = node.expression.arguments[0].elements;
        assert.equal(values.length, 3); assert.equal(values[0].value, 'f'); assert.equal(values[1].value, 0);
        assert.equal(values[2].type, 'FunctionExpression'); exported = values[2];
        operations.push(factory.witness(exported, 'complete153memo Card owner'));
        continue;
      } else if (node.type === 'ExpressionStatement' && call(node.expression, factory.runtime, 'i')) {
        prerequisites.push({ id: node.expression.arguments[0].value, witness: factory.witness(node, 'actual initialized-module prerequisite') });
      } else operations.push(factory.witness(node, `complete local ${node.id?.name ?? node.type}`));
      const cloned = structuredClone(node);
      for (const item of findNodes(cloned, (child) => call(child, factory.runtime, 'i'))) item.callee = { type: 'Identifier', name: 'lookupModule' };
      for (const item of findNodes(cloned, (child) => call(child, factory.runtime, 'A'))) {
        assert.equal(item.arguments.length, 1); assert.equal(item.arguments[0].value, 240916);
        lazy.push(factory.witness(item, 'actual lazy protected-renderer namespace240916'));
        item.callee = { type: 'Identifier', name: 'loadModule' };
      }
      statements.push(code(cloned));
    }
    assert.ok(exported); assert.equal(imports.length, 46); assert.deepEqual(prerequisites.map(({ id }) => id), [12692, 107240]);
    assert.equal(lazy.length, 1);
    assert.equal(findNodes(exported, (node) => call(node, factory.runtime, 'i') || call(node, factory.runtime, 'A')).length, 0);
    const needed = [...imports.map(({ id }) => id), ...prerequisites.map(({ id }) => id)];
    const builder = `function context${builders.length}(lookupModule,loadModule,host){\nconst {window,Date,setTimeout,setInterval,clearInterval}=host;\n${statements.join('\n')}\nconst Card=${code(exported)};\nreturn Object.freeze({Card,MarketCap:x,Media:${names.media},BookmarkControl:${names.bookmark},CharityBadge:${names.charity},LiveBadge:${names.live},MayhemBadge:${names.mayhem},Creator:${names.creator},subscribeClock:${names.subscribe},clockSnapshot:${names.snapshot},clockServerSnapshot:${names.server}});\n}`;
    builders.push(builder);
    contexts.push({ factory: factory.provenance, imports, prerequisites, operations, lazy, needed });
  }
  const admission = await incoming(corpus, factories);
  const ids = contexts[0].needed;
  assert.deepEqual(contexts[1].needed, ids);
  const shared = [352386, 732486, 445242, 705313, 938277, 146695];
  const text = `// Editable complete ordinary MAIN Explore Card and local display/clock owners.\n// Required initialized namespaces/providers/actions stay explicit; captures never execute.\nimport {profileRoute} from '../search-navigation/navigation.mjs';\n${builders.join('\n\n')}\nexport const CARD_CONTEXTS=Object.freeze(${JSON.stringify(PINS.map(([sha]) => sha))});\nexport const MAIN_STATIC_CARD_CONTEXT=${JSON.stringify(admission.cardContexts.find(({ initialScript }) => initialScript).sha256)};\nexport const REQUIRED_MODULES=Object.freeze(${JSON.stringify(ids.filter((id) => !shared.includes(id)))});\nexport function createExploreCoinCard({context,React,jsx,compiler,Avatar,formatters,modules,loadModule,host}){\nif(!CARD_CONTEXTS.includes(context)||typeof React?.useSyncExternalStore!=='function'||typeof jsx?.jsx!=='function'||typeof compiler?.c!=='function'||!Avatar||typeof formatters?.M!=='function'||typeof formatters?.C!=='function'||!(modules instanceof Map)||typeof loadModule!=='function'||!host)throw new TypeError('explicit original Card context/React/Avatar1939format/module/host capabilities required');\nfor(const id of REQUIRED_MODULES)if(!modules.has(id))throw new TypeError('required initialized source namespace '+id);\nfor(const name of ['window','Date','setTimeout','setInterval','clearInterval'])if(!Object.hasOwn(host,name))throw new TypeError('required actual host capability '+name);\nconst owned=new Map([[352386,React],[732486,jsx],[445242,compiler],[705313,{f:Avatar}],[938277,formatters],[146695,{$:profileRoute}]]);\nconst lookupModule=id=>{if(owned.has(id))return owned.get(id);if(!modules.has(id))throw new TypeError('unprovided source namespace '+id);return modules.get(id);};\nreturn(context===CARD_CONTEXTS[0]?context0:context1)(lookupModule,loadModule,host);\n}\n`;
  const navigation = await readFile(path.join(root, 'reconstruction/search-navigation/navigation.mjs'));
  const proof = { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors, admission, contexts,
    acceptedDependency: { path: 'reconstruction/search-navigation/navigation.mjs', sha256: sha256(navigation), symbol: 'profileRoute', actualNamespace: '146695.$' },
    moduleSha256: sha256(text),
    credit: ['OPEN1978 whole actual228998 grid/owner incoming attribution, not copied.', 'OPEN1916 exact original-props Avatar required, implementation not copied.', 'OPEN1939 createLiveCardFormats(context).M/C required compatible API; no compact helper copied or retallied.', 'OPEN1827 actual375676 query/helper provenance; its public pure recomputation facade is NOT substituted for the actual375676.f hook.', 'OPEN1961 OHLC ChartCell is distinct; this Card owns inline SVG projection of provided375676 point data, not that renderer.', 'OPEN1472 clock/relative-time source work remains related; this complete Card factory retains its own actual shared minute-clock source.'],
    transformation: ['Both complete owner variants and all local functions/caches/callbacks/refs/effects/clock operations are separately emitted.', 'Only import/export and lazy namespace lookup become explicit initialized caller capabilities; no original module bootstrap executes.', 'Use one returned flow instance per chosen module context to preserve original shared subscriber/interval lifetime; creating flows is authored composition, not automatic original singleton resolution.', 'Only accepted main profileRoute is imported; open Avatar/formatter/query/action implementations remain explicit required interfaces.'],
    limits: { capturedExecution: false, activeRegistrationWinner: false, originalBootstrap: false, providerImplementation: false, originalAvatarFormatterQuery: false, financialDataAcquisition: false, protectedActionExecution: false, mediaAcquisition: false, originalLazyRenderer: false, tokenDetailPage: false, mountedApp: false, originalCSSVisualParity: false, nativeFinancialCompatibility: false, featureCompletion: false, securityAcceptance: false } };
  return { text, proof };
}

export async function verify(root = APP_ROOT) {
  const result = await recover(root);
  assert.equal(await readFile(path.join(root, DIRECTORY, 'client.mjs'), 'utf8'), result.text, 'complete Explore Card source differs');
  assert.deepEqual(JSON.parse(await readFile(path.join(root, DIRECTORY, 'PROVENANCE.json'), 'utf8')), result.proof, 'Explore Card provenance differs');
  return result.proof;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv[2] === '--write') { const result = await recover(); await mkdir(path.join(APP_ROOT, DIRECTORY), { recursive: true }); await writeFile(path.join(APP_ROOT, DIRECTORY, 'client.mjs'), result.text); await writeFile(path.join(APP_ROOT, DIRECTORY, 'PROVENANCE.json'), JSON.stringify(result.proof, null, 2) + '\n'); }
  else { assert.equal(process.argv[2], '--check'); await verify(); }
  console.log('Complete MAIN Explore Card source PASS');
}
