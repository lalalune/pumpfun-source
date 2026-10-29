import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, propertyName, objectProperty, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = fileURLToPath(new URL('..', import.meta.url));
export const CLIENT = 'reconstruction/create-quote-selection/client.mjs';
export const CONTRACT = 'reconstruction/create-quote-selection/contract.json';
const EXPECTED = [
  [734638, '89ce7de3b9bad421.js', '616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc'],
  [275799, '1147ad0a1bf513f9.js', '65ec0d9fa441ca4402f8e85491e5f26fb5e0a96ac65f2493fb7e4a2e1e659523'],
  [78436, '256f83f9b5d323e6.js', '3293e7177943dd9290ef8ed4c9c65f0174fdfd8d4c7310fe0ad735b239f5e347'],
  [47938, '6a1606765ef3e83e.js', '8f0ac69ea9ce9f4220425f29d1986008bc10174b9bfd3abed6abd23fa06fd8e9'],
  [656846, 'ad7136d0b3a7f323.js', '400cf1cb027f7ca12cc93bf944bc2d6434a099e72c3e1a519f71d6d53c897665'],
  [464649, '3740fc4e7a24596d.js', 'ca7754ff2c723a23029c252c679aad8973c36d1d8b81553d0a29c6ed1c383dda'],
  [464649, 'cf2bb278631744da.js', '79fe88930202bc0145203cb3ea9af220a9b310959f8de0711fa5dfc8ff634145'],
  [187611, 'a0ec47219f76f808.js', 'bd62a3ae8bc3cb897b656e246f762a897468e49c9752cfbe9e82f51de8397c3b'],
  [445242, '01ad4f413e529b60.js', '2d7f3e592645b5e2d997e444ee9b10be6dc8c357680552dccddafb63e4887576'],
  [732486, 'e01139c6299580b1.js', '1327928dc08f8c5ad213c67d8b2b042e579ca141db8b23ac448bf178077cfadd'],
  [789087, '1147ad0a1bf513f9.js', '534813d1de51c339edf0aaca85288ef2001312f7a68d75e62e49d06e9796682f'],
];
const one = (scope, test, label) => exactlyOne(findNodes(scope, test), label);
const print = (node) => generate(node, { comments: false }).code;
const cite = (f, n, label, includeText = true) => ({ ...f.witness(n, label), astType: n.type, ...(includeText ? { text: f.text(n) } : {}) });
const declarations = (f) => f.node.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [n]);
const declaration = (f, name) => exactlyOne(declarations(f).filter((n) => n.id?.name === name), name);
function exported(f, key) {
  const matches = [];
  for (const s of f.node.body.body) {
    const n = s.expression;
    if (n?.type !== 'CallExpression' || n.callee.object?.name !== f.runtime || propertyName(n.callee.property) !== 's' ||
      (n.arguments[1] && n.arguments[1].value !== f.provenance.id)) continue;
    const values = n.arguments[0].elements;
    for (let i = 0; i < values.length; i += 3) if (values[i]?.value === key) matches.push(values[i + 2]);
  }
  return exactlyOne(matches, `export ${f.provenance.id}.${key}`);
}
const resolve = (f, n) => n.type === 'Identifier' ? declaration(f, n.name).init ?? declaration(f, n.name) : n;
const imported = (f, id) => exactlyOne(declarations(f).filter((n) => n.init?.type === 'CallExpression' &&
  n.init.callee.object?.name === f.runtime && n.init.arguments[0]?.value === id), `import ${id}`);

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root), sources = [];
  for (const [id, name, hash] of EXPECTED) {
    const f = await corpus.factory(id, { source: `evidence/web/objects/${name}` });
    assert.equal(f.provenance.sha256, hash, `review changed ${id}/${name}`);
    sources.push(f);
  }
  for (const id of new Set(EXPECTED.map((v) => v[0]))) assert.deepEqual(
    corpus.index.modules.filter((m) => m.ids.includes(id)).map((m) => m.sha256).sort(),
    EXPECTED.filter((v) => v[0] === id).map((v) => v[2]).sort(), `all indexed ${id} variants explicit`);
  const [f, quote, provider, reader, usdc, assetsA, assetsB, formatter, compiler, jsx, mayhem] = sources;
  const controls = ['eq', 'eH', 'ez', 'eL'].map((name) => declaration(f, name));
  assert.deepEqual(controls.map((fn) => one(fn, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    n.arguments[0]?.type === 'NumericLiteral', `memo slots ${fn.id.name}`).arguments[0].value), [62, 10, 6, 15]);
  const [coordinator, radio, icon, gateway] = controls;
  const quoteInit = resolve(quote, exported(quote, 'g')).arguments[0];
  assert.equal(quoteInit.type, 'ArrowFunctionExpression');
  const label = exported(formatter, 'T');
  assert.equal(formatter.text(label), '(e,t)=>e', 'used label dependency is identity; no invented normalization');
  const solanaA = objectProperty(resolve(assetsA, exported(assetsA, 'T')), 'solana');
  const solanaB = objectProperty(resolve(assetsB, exported(assetsB, 'T')), 'solana');
  assert.equal(print(solanaA), print(solanaB), 'both asset contexts agree on selected literal only');
  const usdcImage = objectProperty(resolve(usdc, exported(usdc, 'f')), 'imageUri');
  assert.equal(solanaA.type, 'StringLiteral'); assert.equal(usdcImage.type, 'StringLiteral');
  const parent = one(f.node, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'eq' &&
    n.arguments[1]?.type === 'ObjectExpression' && n.arguments[1].properties.length === 0, 'actual default Create coordinator mount');
  const parentPair = one(f.node, (n) => n.type === 'VariableDeclarator' && n.id?.name === 'E' &&
    n.init?.type === 'CallExpression' && n.init.callee.type === 'SequenceExpression' &&
    n.init.arguments[0]?.type === 'ArrowFunctionExpression' && n.init.arguments[0].body?.property?.name === 'pair', 'actual parent quote state read');
  const picker = declaration(f, 'eM');
  const pickerInputs = one(picker, (n) => n.type === 'VariableDeclarator' && n.id?.type === 'ObjectPattern' &&
    n.id.properties.some((p) => propertyName(p.key) === 'onSelectPumpCoin'), 'external picker body input signature');
  assert.deepEqual(pickerInputs.id.properties.map((p) => propertyName(p.key)), ['isLoading', 'stocks', 'onSelect', 'onSelectPumpCoin', 'onClose']);
  const pickerCall = one(gateway, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'eM', 'gateway to external body');
  const gatewayCall = one(coordinator, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'eL', 'coordinator to complete dialog gateway');
  const stockReaderCall = one(coordinator, (n) => n.type === 'CallExpression' && n.callee.type === 'SequenceExpression' &&
    n.callee.expressions.at(-1)?.object?.name === 'ef', 'actual stocks hook read');
  const disableFlags = one(coordinator, (n) => n.type === 'AssignmentExpression' && n.left.name === 'r' && n.right.type === 'ArrowFunctionExpression', 'complete flag-disable callback');
  const sharing = declaration(f, 'ea');
  const imports = [275799, 445242, 732486, 352386, 398902, 63289, 789087, 47938, 338319, 187611, 928529, 464649, 656846, 34011, 114081, 745018, 439587]
    .map((id) => imported(f, id));
  const code = `export function createQuoteSelectionCoordinator({createBoundStore,React,compiler,jsxRuntime,useTranslation,useStocks,mayhemState,feeSharingState,toast,classes,Image,StockArt,CoinAvatar,Chevron,Dialog,DialogContent,PickerBody}){
    const v={g:createBoundStore(${print(quoteInit)})},m=React,_={c:compiler},t=jsxRuntime,u={f:useTranslation},ef={s:useStocks},R={i:mayhemState},ea=feeSharingState,p={c:toast},ek={c:classes},eA={T:${print(label)}},es={default:Image},f={T:{solana:${print(solanaA)}}},eG={f:{imageUri:${print(usdcImage)}}},en={f:StockArt},ej={CoinAvatar},a={kK:Chevron},i={v:Dialog,s:DialogContent},eM=PickerBody;
    ${controls.map(print).join('\n')}
    return {Control:eq,store:v.g};
  }`;
  const client = '// Complete selected quote coordinator translation; external picker/reader/providers are explicit local ports.\n' +
    '// No original factories, asset search, private Create/H, submission, wallet or service acquisition execute.\n' +
    generate(parse(code, { sourceType: 'module' }), { comments: false }).code + '\n';
  const witnesses = [...imports.map((n) => cite(f, n, 'actual used namespace import')),
    ...controls.map((n) => cite(f, n, `complete selected ${n.id.name} component`)),
    cite(f, parent, 'actual default Create coordinator caller'), cite(f, parentPair, 'actual parent same-store pair read; static only'),
    cite(f, pickerInputs.id, 'external picker body actual five-field input signature'),
    cite(f, picker, 'full external picker context incl search; not emitted or executed', false),
    cite(f, pickerCall, 'actual five-field body handoff, only mounted when open'), cite(f, gatewayCall, 'actual six-field gateway handoff including isOpen'),
    cite(f, stockReaderCall, 'actual always-called reader port'), cite(f, disableFlags.right, 'complete stock-radio flag callback'),
    cite(f, sharing, 'original fee-sharing provider contains private reserve work; inert context only', false),
    cite(quote, quoteInit, 'complete existing quote-store initializer; dependency, no first-recovery claim'),
    cite(provider, exported(provider, '$'), 'existing bound-store API signature; external provider'),
    cite(reader, resolve(reader, exported(reader, 's')), 'external stock query hook signature; no acquisition'),
    cite(reader, declaration(reader, 'h'), 'upstream loader/schema handoff; static only, not implemented', false),
    cite(usdc, usdcImage, 'selected USDC image literal only; no mint/SDK construction'),
    cite(assetsA, solanaA, 'selected SOL image literal in first physical variant'),
    cite(assetsB, solanaB, 'same selected SOL literal in second physical variant'),
    cite(formatter, label, 'existing identity label dependency; no copy-retally claim'),
    cite(compiler, compiler.node, 'compiler bridge; actual runtime supplied', false),
    cite(jsx, jsx.node, 'JSX bridge; actual renderer supplied', false),
    cite(mayhem, exported(mayhem, 'i'), 'Mayhem store export facade; no original store read or execution', false)];
  const contract = { schemaVersion: 1, authority: 'Archived Create source, complete selected coordinator and actual caller/capability handoffs; inert AST only',
    anchors: corpus.anchors, sources: sources.map((s) => s.provenance),
    implementation: { path: CLIENT, sha256: sha256(client), compilerSlots: [62, 10, 6, 15], kind: 'Unmounted quote coordinator and complete radio/icon/dialog gateway' }, witnesses,
    behavior: {
      provider: 'Actual quote initializer: sol default, setPair retains object and derives isQuoteMintEnabled from usdc; setIsQuoteMintEnabled resets sol/usdc pair. Provider API/scheduling external.',
      availability: 'Reader data nullishly falls back to memoized empty array; third radio exists when supplied stocks nonempty OR current pair stock/pump. Pending forwards to picker without disabling other radios.',
      selection: 'Changed stock radio alone runs flag callback then setPair({kind}); same-kind or already stock/pump third-radio click is no-op. SOL/USDC changes do not run flag callback.',
      flags: 'At invocation read supplied getState facades; disable truthy Mayhem, info toast, disable truthy fee-sharing, info toast, then pair setter. No original private initializer, reservation, keys or provider implementation is emitted.',
      stock: 'Picker stock callback stores {kind:stock,stock:input} preserving input identity then closes; it does not repeat radio flag branch.',
      pump: 'Picker Pump callback stores {kind:pump,coin:{...input,name:input.name??input.mint,symbol:input.symbol??input.mint}} then closes; full shallow spread, empty strings retained, no flag branch.',
      gateway: 'Open-state callback ignores true and invokes close on falsy; body only mounted when open. Coordinator-to-gateway six fields; gateway-to-body five fields without isOpen.',
      display: 'Actual radio role/aria-checked, selected-asset prompt/art/translation props, complete inline icon and dialog trigger aria props retained. Images/shared primitives external; no original visual/parity claim.' },
    externalPorts: ['Actual bound-store initializer API and React subscription scheduling', 'Stocks hook () => query result data/isPending; actual47938 reader implementation excluded',
      'Picker body receives five exact callbacks/data fields; its search, eligibility, request construction and service execution excluded',
      'Mayhem and fee-sharing getState/setter facades, translator/toast, class merger, shared art/image/avatar/dialog primitives', 'React useState/compiler/JSX runtime'],
    attribution: ['1884 advanced-fee and1869 base validation/social/dialog remain separate.275799/provider/label/asset source dependencies already attributed; no first recovery or copy-retally claim.',
      'SDK/media681/885/upload1817 unchanged. No absent-main runtime import from open research PRs.'],
    limits: ['No original asset-search, backend/API compatibility, native acquisition, wallet/session/auth, credentials/cookies, private H, Keypair/reservation, fee calculation, submit/upload, instruction/signing or transaction implementation.',
      'Synthetic picker record selection proves callback handoff only, not original search eligibility. Missing/empty Pump name/symbol cases are defensive callback branches, not observed eligible search results.',
      'Source flag setter calls are preserved against supplied local facades; no original provider/resource or launch-admission assurance.',
      'No current assets/prices, original deployment/provider winner, mounted website, whole Create, visual/runtime parity, financial validity, security clearance or milestone claim.'] };
  return { client, contract };
}
export async function verify(root = APP_ROOT, supplied = {}) {
  const actual = await recover(root);
  for (const [key, relative] of [['client', CLIENT], ['contract', CONTRACT]]) {
    const expected = Buffer.from(key === 'client' ? actual.client : JSON.stringify(actual.contract, null, 2) + '\n');
    const bytes = supplied[key] ?? await readFile(path.join(root, relative));
    assert.ok(Buffer.isBuffer(bytes) && bytes.equals(expected), `${relative}: canonical source-derived bytes differ`);
  }
  return { sources: EXPECTED.length, witnesses: actual.contract.witnesses.length, components: 4, compilerSlots: 93, mounted: false };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !['--write', '--check'].includes(mode)) throw Error('Usage: node app/scripts/original-create-quote-selection.mjs --write|--check');
  if (mode === '--write') {
    const { client, contract } = await recover(); await mkdir(path.dirname(path.join(APP_ROOT, CLIENT)), { recursive: true });
    await writeFile(path.join(APP_ROOT, CLIENT), client); await writeFile(path.join(APP_ROOT, CONTRACT), JSON.stringify(contract, null, 2) + '\n');
  }
  console.log(await verify());
}
