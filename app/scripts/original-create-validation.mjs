import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '@babel/generator';
import { parse } from '@babel/parser';
import { openCorpus, findNodes, exactlyOne, propertyName, objectProperty, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = fileURLToPath(new URL('..', import.meta.url));
export const CLIENT = 'reconstruction/create-validation/client.mjs';
export const CONTRACT = 'reconstruction/create-validation/contract.json';
const EXPECTED = [
  [734638, '89ce7de3b9bad421.js', '616b013f89f1cf3e446817865c602c16b9eb6f07e09fa05145c0191ce60f63bc'],
  [586090, '6a1606765ef3e83e.js', '5ddcdce058dfb79522bc03a2ba9bf7d9cae7eccccaad65d80ea43b368f114fc4'],
  [586090, '230764f4d2b8c952.js', 'dc5f49211b3e3c1d2ceb031e2f40ab9d9b327762c059fce10afedabd0b066f9d'],
  [807757, '6a1606765ef3e83e.js', '7094dc3c2113698f06bc9cef420cd9c153d355911226020d467f49a0ad85bf68'],
  [426091, '92f43c917bbc50e2.js', '93b70fac45ba969c312e0f7ec965b181d06a8332f7e1a4bba6751a63fd5555a4'],
];
const print = (node) => generate(node, { comments: false }).code;
const one = (scope, predicate, label) => exactlyOne(findNodes(scope, predicate), label);
const variable = (scope, name) => one(scope, (n) => n.type === 'VariableDeclarator' && n.id?.name === name, `variable ${name}`);
const isJsx = (node, element) => node.type === 'CallExpression' && node.arguments[0]?.value === element &&
  node.arguments[1]?.type === 'ObjectExpression';
function exported(f, key) {
  const matches = [];
  for (const node of findNodes(f.node, (n) => n.type === 'CallExpression' &&
    n.callee.type === 'MemberExpression' && n.callee.object.name === f.runtime &&
    propertyName(n.callee.property) === 's' && n.arguments[0]?.type === 'ArrayExpression')) {
    const values = node.arguments[0].elements;
    for (let i = 0; i < values.length; i += 3) if (values[i]?.value === key) matches.push(values[i + 2]);
  }
  return exactlyOne(matches, `export ${key}`);
}
const cite = (f, node, label, includeText = true) => ({ ...f.witness(node, label), astType: node.type,
  ...(includeText ? { text: f.text(node) } : {}) });
const callName = (node, name) => node.type === 'CallExpression' && node.callee.type === 'Identifier' && node.callee.name === name;

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root);
  const factories = [];
  for (const [id, name, hash] of EXPECTED) {
    const f = await corpus.factory(id, { source: `evidence/web/objects/${name}` });
    assert.equal(f.provenance.sha256, hash, `review changed ${id}/${name}`);
    factories.push(f);
  }
  for (const id of [734638, 586090, 807757, 426091]) {
    assert.deepEqual(corpus.index.modules.filter((m) => m.ids.includes(id)).map((m) => m.sha256).sort(),
      EXPECTED.filter((item) => item[0] === id).map((item) => item[2]).sort(), `indexed ${id} variants must stay explicit`);
  }
  const [f, constants, alternateConstants, bytes, regexes] = factories;
  const html = await corpus.capture('evidence/web/objects/5e15667ed36cac85');
  assert.equal(html.record.sha256, '6568b22a593755b49e02ccc9cb85fdc7655d50e09ccac6d9e0942783ff9f2b26');
  assert.ok(html.text.includes('1d42gkuet1_-2.js'), 'captured /create loads selected physical Create chunk');
  const imports = [586090, 807757, 426091].map((id) => one(f.node, (n) => n.type === 'VariableDeclarator' &&
    n.init?.type === 'CallExpression' && n.init.arguments[0]?.value === id, `used import ${id}`));
  assert.deepEqual(imports.map((n) => n.id.name), ['eX', 'eY', 'X']);
  for (const key of ['O', 'f']) assert.equal(print(exported(constants, key)), print(exported(alternateConstants, key)), 'both constant contexts agree');
  const q = exported(regexes, 'q');
  assert.equal(q.type, 'ObjectExpression');
  assert.deepEqual(q.properties.map((p) => propertyName(p.key)), ['telegram', 'website', 'twitter']);
  assert.ok(q.properties.every((p) => p.value.type === 'RegExpLiteral'));
  const utf8 = exported(bytes, 'W');
  assert.equal(f.text(variable(f.node, 'tn')).startsWith('tn=({decodedJwt:'), true);
  const tn = variable(f.node, 'tn').init;
  assert.equal(tn.body.body.length, 15);
  const bannerLimit = variable(f.node, 'e5');
  const bannerMegabytes = variable(f.node, 'e8');
  const bannerError = variable(f.node, 'ts');
  const social = one(f.node, (n) => n.type === 'VariableDeclarator' && n.id?.name === 'Q' &&
    n.init?.type === 'ArrowFunctionExpression', 'social component');
  const change = one(social.init, (n) => n.type === 'AssignmentExpression' && n.left.name === 'a' &&
    n.right.type === 'ArrowFunctionExpression', 'complete social change callback').right;
  const blur = one(social.init, (n) => n.type === 'AssignmentExpression' && n.left.name === 'i' &&
    n.right.type === 'ArrowFunctionExpression', 'complete social blur callback').right;
  const initialErrors = one(social.init, (n) => n.type === 'ObjectExpression' &&
    n.properties.length === 3 && n.properties.every((p) => p.value?.type === 'StringLiteral' && p.value.value === ''), 'initial social errors');
  const socialInputs = ['website', 'twitter', 'telegram'].map((key) => one(social.init, (n) => isJsx(n, 'input') &&
    n.arguments[1].properties.some((p) => propertyName(p.key) === 'id' && p.value.value === key), `${key} input`));
  const socialWrappers = ['n', 'o', 'p', 'x', 'v', 'w'].map((name) => one(social.init, (n) =>
    n.type === 'AssignmentExpression' && n.left.name === name && n.right.type === 'ArrowFunctionExpression', `${name} social input wrapper`).right);
  const errorConsumers = ['website', 'twitter', 'telegram'].map((key) => one(social.init, (n) => n.type === 'LogicalExpression' &&
    n.left.type === 'MemberExpression' && n.left.object.name === 'L' && propertyName(n.left.property) === key &&
    isJsx(n.right, 'span'), `${key} error span`));
  const component = one(f.node, (n) => n.type === 'FunctionExpression' && !n.id && n.start > 40490 && n.start < 40800, 'actual default Create component');
  const textInputs = ['name', 'ticker'].map((key) => one(component, (n) => isJsx(n, 'input') &&
    n.arguments[1].properties.some((p) => propertyName(p.key) === 'id' && p.value.value === key), `${key} input`));
  const description = one(component, (n) => isJsx(n, 'textarea'), 'description input');
  const textHandlers = [...textInputs, description].map((n) => objectProperty(n.arguments[1], 'onChange'));
  const socialCaller = one(component, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'Q' &&
    n.arguments[1]?.type === 'ObjectExpression', 'actual social component caller');
  const hCaller = one(component, (n) => n.type === 'CallExpression' && n.arguments[0]?.name === 'H' &&
    n.arguments[1]?.type === 'ObjectExpression', 'actual confirmation component caller');
  const parentValidate = objectProperty(hCaller.arguments[1], 'validate');
  const calls = findNodes(component, (n) => callName(n, 'tn'));
  assert.equal(calls.length, 2, 'both actual validator callers');
  assert.equal(f.text(calls[0].arguments[0]), f.text(calls[1].arguments[0]), 'same thirteen fields at dialog and later submit');
  const fieldBindings = calls[0].arguments[0].properties.map((p) => [propertyName(p.key), p.value.name]);
  assert.equal(fieldBindings.length, 13);
  const submitTry = one(component, (n) => n.type === 'TryStatement' && n.block.body.length === 1 &&
    n.block.body[0].type === 'ExpressionStatement' && callName(n.block.body[0].expression, 'tn'), 'later pre-upload validation catch');
  const dialog = one(f.node, (n) => n.type === 'FunctionDeclaration' && n.id?.name === 'H', 'private dialog component context');
  const opening = variable(dialog, 'em').init;
  assert.equal(opening.type, 'CallExpression');
  assert.equal(opening.arguments[0].async, true);
  assert.equal(f.text(opening.arguments[1]), '[S,_,O]');
  const dialogJsx = one(dialog, (n) => n.type === 'CallExpression' && n.arguments[0]?.type === 'MemberExpression' &&
    n.arguments[0].object.name === 'L' && propertyName(n.arguments[0].property) === 'N', 'dialog direct state binding');
  assert.equal(objectProperty(dialogJsx.arguments[1], 'onOpenChange').name, 'T');
  const button = one(dialog, (n) => n.type === 'CallExpression' && n.arguments[1]?.type === 'ObjectExpression' &&
    n.arguments[1].properties.some((p) => propertyName(p.key) === 'onClick' && p.value.name === 'em'), 'actual opener button');
  const enabled = variable(dialog, 'K');
  const walletUIBinding = one(dialog, (n) => n.type === 'VariableDeclarator' && n.id?.type === 'ObjectPattern' &&
    n.id.properties.some((p) => propertyName(p.key) === 'wallet'), 'private wallet availability input; static only');
  const availabilityBinding = one(component, (n) => n.type === 'VariableDeclarator' && n.id?.type === 'ObjectPattern' &&
    n.id.properties.some((p) => propertyName(p.key) === 'decodedJwt'), 'parent truthiness availability input; static only');
  const stateBindings = ['e_', 'ey', 'ew', 'ej', 'eT', 'ek'].map((name) => one(component, (n) =>
    n.type === 'VariableDeclarator' && n.id?.type === 'ArrayPattern' && n.id.elements[0]?.name === name, `field state ${name}`));
  const media = one(component, (n) => n.type === 'ArrowFunctionExpression' && n.start === 41201 && n.end === 45619, 'captured media hook context only');
  const statusState = one(media, (n) => n.type === 'VariableDeclarator' && n.id?.type === 'ArrayPattern' &&
    n.id.elements[0]?.name === 'C', 'preview status initialization');
  const statusCalls = findNodes(media, (n) => callName(n, 'T'));
  assert.deepEqual(statusCalls.map((n) => f.text(n)), ['T(0)'], 'only captured preview status reset; status2 not shown reachable');
  const mediaReturn = one(media.body, (n) => n.type === 'ObjectExpression' &&
    n.properties.some((p) => propertyName(p.key) === 'previewStatus'), 'media result field bindings');
  assert.ok(!mediaReturn.properties.some((p) => propertyName(p.key) === 'setPreviewStatus'));
  const fieldsPattern = `{${fieldBindings.map(([key, value]) => `${key}:${value}`).join(',')}}`;
  const template = `export function createFieldValidator({ utf8Bytes }) {\n  const eY = { W: utf8Bytes };\n  const eX = { O: ${print(exported(constants, 'O'))}, f: ${print(exported(constants, 'f'))} };\n  const X = { q: ${print(q)} };\n  const ${print(bannerLimit)}, ${print(bannerMegabytes)};\n  const ${print(bannerError)};\n  return ${print(tn)};\n}\n\nexport function createParentValidate(snapshot, { validateFields: tn, translate: e, toast: p }) {\n  const ${fieldsPattern} = snapshot;\n  return ${print(parentValidate)};\n}\n\nexport function createTextCallbacks({ setName: eg, setTicker: ev, setDescription: eE }) {\n  return { name: ${print(textHandlers[0])}, ticker: ${print(textHandlers[1])}, description: ${print(textHandlers[2])} };\n}\n\nexport function initialSocialErrors() { return ${print(initialErrors)}; }\n\nexport function createSocialCallbacks({ setTelegram: O, setWebsite: P, setTwitter: R, setErrors: M }) {\n  const X = { q: ${print(q)} };\n  const D = ${print(change)};\n  const F = ${print(blur)};\n  return { website: { onChange: ${print(socialWrappers[0])}, onBlur: ${print(socialWrappers[1])} },\n    twitter: { onChange: ${print(socialWrappers[2])}, onBlur: ${print(socialWrappers[3])} },\n    telegram: { onChange: ${print(socialWrappers[4])}, onBlur: ${print(socialWrappers[5])} } };\n}\n\nexport function createDialogCallbacks({ walletAvailable: S, validate: _, setDialogOpen: T, setDialogError: A, requestWalletUI: O, telemetry: F, logger: console }) {\n  return { onClick: ${print(opening.arguments[0])}, onOpenChange: T };\n}\n`;
  const client = '// Reconstructed selected nonmutating callbacks; authenticated inert AST, never whole captured modules.\n' +
    '// Explicit local capabilities and render snapshots only; no React, wallet, submit or upload execution.\n' +
    generate(parse(template, { sourceType: 'module' }), { comments: false }).code + '\n';
  const sourceNodes = [
    ...imports.map((n) => cite(f, n, 'actual used namespace import')),
    cite(f, bannerLimit, 'banner size alias'), cite(f, bannerMegabytes, 'banner copy scale'), cite(f, bannerError, 'banner error copy'),
    cite(f, tn, 'complete ordered thirteen-field validator; success undefined'),
    ...stateBindings.map((n) => cite(f, n, 'actual parent field state')),
    ...textInputs.map((n) => cite(f, n, 'actual text input including UTF-16 change admission and ticker maxLength')),
    cite(f, description, 'description raw setter consumer'),
    cite(f, socialCaller, 'actual social value/setter caller'), cite(f, initialErrors, 'initial social error state'),
    cite(f, change, 'complete raw social change and clear-one-error callback'), cite(f, blur, 'complete social blur-only error update'),
    ...socialWrappers.map((n) => cite(f, n, 'actual input field callback binding')),
    ...socialInputs.map((n) => cite(f, n, 'actual social input value/change/blur consumer')),
    ...errorConsumers.map((n) => cite(f, n, 'actual conditional social error consumer')),
    cite(f, hCaller, 'actual parent confirmation caller with all thirteen validation fields'),
    cite(f, parentValidate, 'complete parent validation/toast callback; false only on caught failure'),
    cite(f, opening, 'complete async opening callback and original useCallback dependencies'),
    cite(f, objectProperty(dialogJsx.arguments[1], 'open'), 'dialog open-state value'),
    cite(f, objectProperty(dialogJsx.arguments[1], 'onOpenChange'), 'dialog direct state setter callback'),
    cite(f, button, 'actual opening button consumer; disabled gate remains static only'),
    cite(f, enabled, 'private wallet/financial button admission; static only'),
    cite(f, walletUIBinding, 'original private wallet availability binding; not implemented or read'),
    cite(f, availabilityBinding, 'original parent decodedJwt binding; opaque supplied truthiness only'),
    cite(f, dialog, 'whole private confirmation context NOT emitted or executed', false),
    ...calls.map((n) => cite(f, n, 'both used validator calls with identical field mapping')),
    cite(f, submitTry, 'later submission revalidation returns on error before upload; static only'),
    cite(f, statusState, 'media hook preview status initializes zero; static only'),
    ...statusCalls.map((n) => cite(f, n, 'only captured preview status setter call resets zero; static only')),
    cite(f, mediaReturn, 'actual media object field handoff; no preview-status setter exposed', false),
  ];
  const dependencies = factories.slice(1).map((source, i) => ({ factory: source.provenance, sourceNodes:
    i < 2 ? ['O', 'f'].map((key) => cite(source, exported(source, key), `declared ${key} constants`)) :
      [cite(source, i === 2 ? utf8 : q, i === 2 ? 'existing UTF-8 byte helper; external supplied port, not copied' : 'complete three social RegExp validators')] }));
  const contract = {
    schemaVersion: 1,
    authority: 'Captured /create source parsed as inert AST; selected nonmutating callback transcription with explicit synthetic capabilities',
    anchors: corpus.anchors,
    route: { record: html.record, binding: 'HTML names selected 1d42gkuet1_-2.js chunk; Googlebot archived context, not authenticated/current deployment evidence' },
    implementation: { path: CLIENT, sha256: sha256(client), kind: 'Selected callback source model, not whole captured component or mounted UI' },
    create: { factory: f.provenance, sourceNodes }, dependencies,
    fields: fieldBindings.map(([field, binding]) => ({ field, binding })),
    behavior: {
      textChanges: 'Name admits raw value.length<=32, ticker<=10; ticker maxLength10 separately declared; description raw setter; no trimming/normalization.',
      validation: 'Complete tn: truthy supplied availability, required name/ticker, external UTF-8 byte limits32/10, description UTF-16 length2000, media sizes4500000/10000000/4500000, media/thumbnail readiness, ordered social regex gates. First Error wins; success undefined.',
      social: 'Change sets one raw value then clears only its error; blur changes only errors via functional updater; empty/undefined blur clears; actual conditional spans consume errors. Blur and tn have intentionally different error copy and website guards.',
      parent: 'Render-snapshot field bindings captured once; success undefined; caught failure calls translate then toast.c.error preserving receiver, returns false; reporter failures escape.',
      dialog: 'Explicit supplied wallet availability: absent emits telemetry then requests wallet UI and returns; present calls validate synchronously without inspecting/awaiting result, then opens and clears error. Catch logs then stores Error.message or fallback. onOpenChange is direct supplied setter.',
      laterRevalidation: 'Actual later submit calls same validator in try/catch and returns on error before upload; recorded statically only. Dialog false-return behavior is preserved without vulnerability or backend/admission claim.',
      previewStatus: 'Validator has literal status2 bypass; captured media hook initializes0, only T(0) setter call and no exported setter. A supplied2 model case is synthetic branch coverage, not observed reachability.',
    },
    boundaries: [
      'No Zod/schema engine here: tn is ordered JavaScript truthiness/length/size/RegExp checks; file type, nonempty bytes, social length, type repair and server admission are not added.',
      'decodedJwt is an opaque supplied truthiness flag only; walletAvailable is independently supplied UI availability. Neither reads or validates a wallet, session or credential.',
      'UTF-8 helper807757.W is already attributed in open1424; its exact value=>byteCount signature is an explicit caller capability because that PR is absent from this main. No implicit dependency or new helper credit.',
      'Existing681/885 media bindings,1817 upload handoffs and local offline create form policy remain separate and unchanged.',
      'Whole H includes private Keypair, lease, amount, funding and submit work and is never emitted/executed; React compiler memo caches/scheduler, disabled financial gate, reset and transaction callbacks stay static context.',
      'No actual toast, telemetry, wallet UI, translation provider, upload, HTTP, signing, submit, original bundle execution, native compatibility, mounted UI or milestone result is qualified.',
    ],
  };
  return { client, contract };
}

export async function verify(root = APP_ROOT, supplied = {}) {
  const recovered = await recover(root);
  for (const [key, relative] of [['client', CLIENT], ['contract', CONTRACT]]) {
    const expected = Buffer.from(key === 'client' ? recovered.client : JSON.stringify(recovered.contract, null, 2) + '\n');
    const actual = supplied[key] ?? await readFile(path.join(root, relative));
    assert.ok(Buffer.isBuffer(actual) && actual.equals(expected), `${relative}: canonical UTF-8 bytes differ from authenticated output`);
  }
  return { factories: EXPECTED.length, validationCallers: 2, fields: 13, witnesses: recovered.contract.create.sourceNodes.length + recovered.contract.dependencies.reduce((n, d) => n + d.sourceNodes.length, 0) };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !['--write', '--check'].includes(mode)) throw Error('Usage: node app/scripts/original-create-validation.mjs --write|--check');
  if (mode === '--write') {
    const { client, contract } = await recover();
    await mkdir(path.dirname(path.join(APP_ROOT, CLIENT)), { recursive: true });
    await writeFile(path.join(APP_ROOT, CLIENT), client);
    await writeFile(path.join(APP_ROOT, CONTRACT), JSON.stringify(contract, null, 2) + '\n');
  }
  console.log(await verify());
}
