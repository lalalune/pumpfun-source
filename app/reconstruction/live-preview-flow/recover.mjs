import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, member, sha256 } from '../../scripts/original-contracts/source.mjs';
import { parseFlightRecords } from '../../scripts/settings-client-contract.mjs';

export const APP_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const DIRECTORY = 'reconstruction/live-preview-flow';
const contexts = [
  [31113, 'aa72011769a3'], [133244, '248fcf72a5bb'], [369731, 'fc87a2c85f17'],
  [41705, 'f48d711e57f9'], [56999, 'b147f59a3399'], [798394, 'e575a7a694ec'],
  [218921, '7741ad9f49b1'], [187807, '35481d754b13'], [47367, '370927cfabd7'],
  [971491, 'a27d34c42bdf'], [773918, '2a42d2873a80'], [202541, '634fb6385be3'],
];
const specs = [
  { id: 56999, name: 'buildMute', groups: [56999] },
  { id: 798394, name: 'buildScroll', groups: [798394, 70678, 65769], dom: ['ResizeObserver', 'MutationObserver'] },
  { id: 187807, name: 'buildStage', groups: [187807, 829010] },
  { id: 218921, name: 'buildPagination', groups: [218921] },
  { id: 41705, name: 'buildPreview', groups: [816882, 41705], locals: ['m', 'u', 'x'], importBeforeLocal: 'x' },
  { id: 369731, name: 'buildHero', groups: [369731], dom: ['document'] },
];
const code = (node) => generate(node, { comments: false }).code;
const tops = (f) => f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : []);
const isImport = (f, d) => d.init?.type === 'CallExpression' && member(d.init.callee, f.runtime, 'i');
function registrations(f) {
  return findNodes(f.node, (n) => n.type === 'CallExpression' && member(n.callee, f.runtime, 's')).map((n) => {
    assert.equal(n.arguments[0].type, 'ArrayExpression');
    const group = n.arguments[1]?.value ?? (assert.equal(f.ids.length, 1), f.id);
    const a = n.arguments[0].elements, entries = [];
    for (let i = 0; i < a.length;) {
      assert.equal(a[i].type, 'StringLiteral'); const name = a[i++].value;
      if (a[i]?.type === 'NumericLiteral') { assert.equal(a[i++].value, 0); entries.push({ name, value: a[i++] }); }
      else { const getter = a[i++]; assert.equal(getter.type, 'ArrowFunctionExpression'); assert.equal(getter.params.length, 0);
        assert.notEqual(getter.body.type, 'BlockStatement'); entries.push({ name, value: getter.body, getter }); }
    }
    return { group, entries, node: n };
  });
}
const resolve = (f, node) => node.type === 'Identifier' ? exactlyOne(tops(f).filter((d) => d.id.name === node.name), `local ${node.name}`).init : node;
const exported = (f, id, name) => resolve(f, exactlyOne(registrations(f).filter((r) => r.group === id), `registration ${id}`).entries.find((e) => e.name === name).value);

async function originContext(corpus, selected) {
  const html = await corpus.capture('evidence/web/objects/c45d40b52df03727');
  assert.equal(html.record.url, 'https://pump.fun/live'); assert.equal(html.record.final_url, html.record.url);
  const pushes = [...html.text.matchAll(/<script>self\.__next_f\.push\(([\s\S]*?)\)<\/script>/g)]
    .map((match) => ({ match, value: JSON.parse(match[1]) })).filter(({ value }) => value.length === 2 && value[0] === 1 && typeof value[1] === 'string');
  assert.equal(pushes.length, 1); const stream = pushes[0].value[1], records = parseFlightRecords(stream);
  assert.equal(records.get('116').kind, 'import'); assert.equal(records.get('116').value[0], 31113);
  assert.equal(records.get('116').value[2], 'LiveHomepage');
  const elements = [];
  function findElement(value, trail = []) {
    if (!value || typeof value !== 'object') return;
    if (Array.isArray(value) && value[0] === '$' && value[1] === '$L116') elements.push({ value, trail });
    for (const [key, child] of Object.entries(value)) findElement(child, [...trail, key]);
  }
  findElement(records.get('7f').value); assert.equal(elements.length, 1, 'actual nested main-page element');
  const element = elements[0].value;
  assert.deepEqual(Object.keys(element[3]), ['initialHeroData', 'initialSectionData']); assert.equal(element[3].initialHeroData.length, 6);
  const scripts = new Set([...html.text.matchAll(/<script\b[^>]*src="([^"]+)"/g)].map((m) => new URL(m[1], html.record.url).href));
  const initial = [31113, 133244, 369731, 41705].map((id) => {
    const f = selected.get(id); assert.ok(scripts.has(f.provenance.url)); assert.equal(new URL(f.provenance.url).origin, 'https://pump.fun');
    return { id, source: f.provenance.source, url: f.provenance.url };
  });
  return { source: html.record.path, url: html.record.url, sha256: html.record.sha256, bytes: html.record.bytes,
    push: html.witness({ start: pushes[0].match.index, end: pushes[0].match.index + pushes[0].match[0].length }, 'actual main /live Flight push'),
    decodedFlightSha256: sha256(stream), importRow: '116', elementRow: '7f', elementPath: elements[0].trail, component: 'LiveHomepage', initialScripts: initial,
    limit: 'Captured main-page context only. Initial data is not replayed here; no lazy execution, active runtime winner, current stream or playback proof.' };
}

const adapter = `
// Authored capability composition. Original module-loader caching, dynamic
// scheduling, providers and media behavior are outside this boundary.
export function createLivePreviewFlow({ React, jsx, compiler, modules, loadPreview, dom }) {
  if (!React || typeof React.useState !== 'function' || typeof jsx?.jsx !== 'function' ||
      typeof compiler?.c !== 'function' || typeof loadPreview !== 'function' || !modules ||
      !dom || typeof dom.document?.addEventListener !== 'function' ||
      typeof dom.ResizeObserver !== 'function' || typeof dom.MutationObserver !== 'function')
    throw new TypeError('explicit React/JSX/compiler, module, preview-loader and DOM capabilities are required');
  const owned = new Map([[352386, React], [732486, jsx], [445242, compiler]]);
  const imports = (id) => {
    if (owned.has(id)) return owned.get(id);
    if (!Object.hasOwn(modules, id)) throw new TypeError('missing explicit module capability ' + id);
    return modules[id];
  };
  for (const build of [buildMute, buildScroll, buildStage, buildPagination, buildPreview, buildHero])
    for (const [id, value] of Object.entries(build(imports, dom, loadPreview))) owned.set(Number(id), value);
  return Object.freeze({ HeroCarousel: owned.get(369731).HeroCarousel,
    VideoMuteProvider: owned.get(56999).c, useVideoMute: owned.get(56999).F,
    PreviewMedia: owned.get(41705).f, MuteButton: owned.get(816882).f,
    PaginationDots: owned.get(218921).PaginationDots });
}
`;

export async function buildPreviewFlow(root = APP_ROOT) {
  const corpus = await openCorpus(root), selected = new Map(), factories = [], fragments = [], imports = [], components = [];
  for (const [id, prefix] of contexts) {
    const variants = corpus.index.modules.filter((m) => m.ids.includes(id)); assert.equal(variants.length, 1, `physical variant census ${id}`);
    assert.equal(variants[0].origins.length, 1, `physical context census ${id}`); assert.ok(variants[0].sha256.startsWith(prefix));
    const f = await corpus.factory(id); selected.set(id, f); factories.push(f.provenance);
  }
  const witness = (f, node, label) => { const w = f.witness(node, label); fragments.push(w); return w; };
  const blocks = [];
  for (const spec of specs) {
    const f = selected.get(spec.id), variables = tops(f), values = [];
    const limit = spec.importBeforeLocal ? exactlyOne(variables.filter((d) => d.id.name === spec.importBeforeLocal), 'preview import cutoff').start : Infinity;
    for (const d of variables.filter((d) => isImport(f, d) && d.start < limit)) {
      assert.equal(d.init.arguments.length, 1); assert.equal(d.init.arguments[0].type, 'NumericLiteral');
      imports.push({ factoryId: spec.id, alias: d.id.name, moduleId: d.init.arguments[0].value, ...witness(f, d, `actual ${spec.id} import ${d.init.arguments[0].value}`) });
      values.push(`var ${d.id.name} = imports(${d.init.arguments[0].value});`);
    }
    for (const statement of f.node.body.body) {
      if (statement.type === 'VariableDeclaration') {
        const declarations = statement.declarations.filter((d) => !isImport(f, d) && (!spec.locals || spec.locals.includes(d.id.name)));
        if (!declarations.length) continue;
        for (const d of declarations) witness(f, d, `complete ${spec.id} local ${d.id.name}`);
        const copy = structuredClone({ ...statement, declarations });
        // The sole recovered lazy-preview call becomes an explicit loader port.
        // No captured runtime or inner player implementation is loaded/evaluated.
        const lazy = findNodes(copy, (n) => n.type === 'CallExpression' && member(n.callee, f.runtime, 'A'));
        for (const n of lazy) { assert.equal(spec.id, 41705); assert.equal(n.arguments.length, 1); assert.equal(n.arguments[0].value, 47367);
          n.callee = { type: 'Identifier', name: 'loadPreview' }; }
        values.push(code(copy));
      } else if (statement.type === 'FunctionDeclaration') { witness(f, statement, `complete ${spec.id} local function ${statement.id.name}`); values.push(code(statement)); }
    }
    const groups = [];
    for (const id of spec.groups) {
      const r = exactlyOne(registrations(f).filter((r) => r.group === id), `selected group ${id}`);
      const fields = r.entries.map((entry) => {
        witness(f, entry.value, `complete ${id}.${entry.name} export value`);
        const fn = resolve(f, entry.value); if (['ArrowFunctionExpression', 'FunctionExpression'].includes(fn?.type))
          components.push({ factoryId: spec.id, moduleId: id, name: entry.name, ...f.witness(fn, `complete selected ${id}.${entry.name}`) });
        return `${JSON.stringify(entry.name)}: ${code(entry.value)}`;
      });
      groups.push(`${id}: {${fields.join(',\n')}}`);
    }
    blocks.push(`function ${spec.name}(imports, dom, loadPreview) {\n${spec.dom ? `const {${spec.dom.join(',')}} = dom;\n` : ''}${values.join('\n')}\nreturn {${groups.join(',\n')}};\n}`);
  }
  const text = `// Editable source-adapted main /live outer preview components.\n// Regenerate/check with recover.mjs; captured factories are never evaluated.\n${blocks.join('\n\n')}\n${adapter}`;
  const parent = selected.get(31113), query = selected.get(133244), loader = selected.get(47367), entry = selected.get(971491), player = selected.get(773918);
  for (const [f, id, name] of [[parent,31113,'LiveHomepage'],[query,133244,'_'],[player,773918,'LivestreamPreviewPlayer']])
    witness(f, exported(f,id,name), `source-bound context/explicit capability ${id}.${name}; not implemented by this unit`);
  witness(loader, loader.node, 'complete actual preview lazy chunk list; not executed');
  witness(entry, entry.node, 'actual 971491 forwarder to 773918; not executed');
  const contextEdges = [];
  for (const [from,to,name,limit] of [[31113,133244,'_','main-page hero render'],
    [133244,859960,'L','reused listing/query capability; not implemented'],[133244,369731,'HeroCarousel','actual queried-data render'],
    [369731,41705,'f','selected-slide media-prop handoff'],[369731,56999,'F','actual HeroSlide mute context'],
    [41705,325320,'t','provider wrapper port only; auth/join/presence not implemented'],
    [41705,405048,'V','metadata wrapper port only'],[41705,425444,'default','image component port only'],
    [41705,369091,'useIpfsPrefix','configured URI-prefix port only']]) {
    const f=selected.get(from),binding=exactlyOne(tops(f).filter((d)=>isImport(f,d)&&d.init.arguments[0].value===to),`actual context import ${from}→${to}`);
    const calls=findNodes(f.node,(n)=>n.type==='CallExpression'&&(member(n.callee,binding.id.name,name)||
      n.callee?.type==='SequenceExpression'&&member(n.callee.expressions.at(-1),binding.id.name,name)||member(n.arguments[0],binding.id.name,name)));
    assert.ok(calls.length>0,`actual context use ${from}→${to}.${name}`);
    contextEdges.push({from,to,name,limit,import:f.witness(binding,`actual ${from}→${to} import`),
      calls:calls.map((call)=>f.witness(call,`actual ${from}→${to}.${name} handoff`))});
  }
  const lazyAssets=[];
  for(const value of findNodes(loader.node,(n)=>n.type==='StringLiteral'&&n.value.startsWith('static/immutable/chunks/'))){
    const url=new URL(value.value,'https://pump.fun/_next/').href;
    const record=exactlyOne(corpus.manifest.records.filter((r)=>r.url===url&&r.status===200),`retained lazy asset ${url}`);
    const asset=await corpus.capture(record.path);lazyAssets.push({path:record.path,url,sha256:record.sha256,bytes:asset.bytes.length});
  }
  assert.equal(lazyAssets.length,7);
  const proof = { schemaVersion: 1, baseCommit: '094a06f18df738d41e77070c1a009e135671ac1a', anchors: corpus.anchors,
    origin: await originContext(corpus,selected), generatedSha256: sha256(text), factories, fragments, components, imports, contextEdges, lazyAssets,
    transformation: { unchanged: 'Complete selected declarations/component callback bodies, including compiler memo-cache slots and every state/effect/event operation.',
      changed: ['actual imports become explicit module capabilities', 'selected exports become a returned object', 'sole preview runtime A(47367) becomes loadPreview(47367)', 'document/ResizeObserver/MutationObserver bind explicit DOM capabilities'],
      excluded: ['style-only imports 12692/137793', 'unselected quick-trade and badge/metadata widget bodies in grouped 816882 factory', 'inner player, LiveKit/token/join/provider implementation', 'original module/runtime scheduling/caching'] },
    limits: { capturedExecution: false, serviceAcquisition: false, mediaAcquisition: false, credentials: false, innerPlayer: false,
      authOrJoin: false, nativePlayback: false, mountedApplication: false, originalVisualParity: false, progressCredit: false } };
  return { text, proof };
}
export async function verifyPreviewFlow(root = APP_ROOT) {
  const {text,proof} = await buildPreviewFlow(root);
  assert.equal(await readFile(path.join(root,DIRECTORY,'components.mjs'),'utf8'),text,'editable preview components differ from complete source adaptation');
  assert.deepEqual(JSON.parse(await readFile(path.join(root,DIRECTORY,'PROVENANCE.json'),'utf8')),proof,'preview source provenance differs');
  return proof;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv[2] === '--write') { const {text,proof}=await buildPreviewFlow(); await mkdir(path.join(APP_ROOT,DIRECTORY),{recursive:true});
    await writeFile(path.join(APP_ROOT,DIRECTORY,'components.mjs'),text); await writeFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),JSON.stringify(proof,null,2)+'\n'); }
  else { assert.equal(process.argv[2],'--check'); await verifyPreviewFlow(); }
  console.log('Main /live outer preview source PASS');
}
