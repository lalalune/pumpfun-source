import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openCorpus, findNodes, exactlyOne, propertyName, objectProperty, literal, sha256 } from './original-contracts/source.mjs';

export const APP_ROOT = fileURLToPath(new URL('..', import.meta.url));
export const OUTPUT = 'reconstruction/verified-profile/contract.json';
const EXPECTED = [
  {
    "label": "readerA",
    "id": 179736,
    "source": "evidence/web/objects/da58569257a3fbc5.js",
    "sha256": "65c55fd94aae19033823800ac95d722d88c4cd549c869927bfe53b6b675596f1"
  },
  {
    "label": "readerB",
    "id": 179736,
    "source": "evidence/web/objects/c7e25d5561f3a8f8.js",
    "sha256": "8b4fa23b4c652bb17188ff843e8878e509e6f1bb661a7ccefea3d84710cf150b"
  },
  {
    "label": "identityA",
    "id": 154121,
    "source": "evidence/web/objects/2d59b7c63a95235e.js",
    "sha256": "69d4913a99ac03b7dc65976128f0553c650a3c9bb8edbf7f6d2b76e7761cf175"
  },
  {
    "label": "identityB",
    "id": 154121,
    "source": "evidence/web/objects/2d2e035b6050f6bd.js",
    "sha256": "4645905f821dbfcd53e6c8619b498b93aba721329ed0dfc56ffffaaaad64111e"
  },
  {
    "label": "identityC",
    "id": 154121,
    "source": "evidence/web/objects/c02c04ce3dfbfd3c.js",
    "sha256": "9aa2c92333b585552d7a2f25234b8db68e58fcc14d45200f44a7ae82d62f3ca2"
  },
  {
    "label": "identityD",
    "id": 154121,
    "source": "evidence/web/objects/c7e25d5561f3a8f8.js",
    "sha256": "c78cd179db685f96d2d795d7a7793a0e49efca5b1fc9212d2b2ebe53c9229abc"
  },
  {
    "label": "renderer",
    "id": 693124,
    "source": "evidence/web/objects/eb0b23ee6feb7543.js",
    "sha256": "4b94aa99e04cf92a4e2a79379d9c2336e2ea9f81d3ba90ff5433452a04e30a4d"
  },
  {
    "label": "chains",
    "id": 646908,
    "source": "evidence/web/objects/1e479323ffe53c14.js",
    "sha256": "719f637fc436bde35bcaa1da5eac3057212d49b84331e27068450218041eb6c0"
  },
  {
    "label": "nearA",
    "id": 253623,
    "source": "evidence/web/objects/eb0b23ee6feb7543.js",
    "sha256": "24448702f9d61cc35693127b9b37f6ccff6a40a2f552cbd545d647895e93ad10"
  },
  {
    "label": "nearB",
    "id": 253623,
    "source": "evidence/web/objects/a06b86c38599958e.js",
    "sha256": "432437430647542a633eb57061d43b3d1c5683bcbaf5a68e158e33918ff3ade0"
  },
  {
    "label": "evm",
    "id": 605587,
    "source": "evidence/web/objects/2c867fef5c76d400.js",
    "sha256": "bceabd6341b002dbe14334459e7470c27ca90281762d8c10db07ed3044f57ea1"
  },
  {
    "label": "websiteConstructor",
    "id": 30181,
    "source": "evidence/web/objects/01ad4f413e529b60.js",
    "sha256": "fbae4e508e6c986c68209d975d3eea247718d478272089a60504b776074e2413"
  },
  {
    "label": "registry",
    "id": 402030,
    "source": "evidence/web/objects/2b47dd0b38a1608f.js",
    "sha256": "26d7d7ced2e06fee3c9354e5ffd9626bcf4f953c8927d3a5ea43d5a45e7064c2"
  },
  {
    "label": "transport",
    "id": 898661,
    "source": "evidence/web/objects/2b47dd0b38a1608f.js",
    "sha256": "9015e4bad4b1f0bb4b245e446689d9b7e939b3ba922044c82dcd9e8d5f3d9ed5"
  },
  {
    "label": "declaration",
    "id": 850620,
    "source": "evidence/web/objects/2b47dd0b38a1608f.js",
    "sha256": "9d34ea015ae0110705115ca39ada259843ffeffe34262f5487220be4b6aaa57f"
  }
];
const unsequence = (n) => n?.type === 'SequenceExpression' ? n.expressions.at(-1) : n;
const memberCall = (n, object, property) => n.type === 'CallExpression' &&
  unsequence(n.callee)?.type === 'MemberExpression' &&
  unsequence(n.callee).object.name === object && propertyName(unsequence(n.callee).property) === property;
function exported(f, id, key) {
  const values = [];
  for (const n of findNodes(f.node, (n) => n.type === 'CallExpression' &&
    n.callee.type === 'MemberExpression' && n.callee.object.name === f.runtime &&
    propertyName(n.callee.property) === 's' && n.arguments[0]?.type === 'ArrayExpression' &&
    (n.arguments[1]?.value === id || (!n.arguments[1] && f.ids.includes(id))))) {
    const a = n.arguments[0].elements;
    for (let i = 0; i < a.length; i += 3) if (a[i]?.value === key) values.push(a[i + 2]);
  }
  return exactlyOne(values, `${id}.${key} export`);
}
function declarations(scope) {
  return scope.body.body.flatMap((n) => n.type === 'VariableDeclaration' ? n.declarations : [n]);
}
function resolve(f, n) {
  if (n.type !== 'Identifier') return n;
  const found = exactlyOne(declarations(f.node).filter((d) => d.id?.name === n.name), `local ${n.name}`);
  return found.init ?? found;
}
function imported(f, id) {
  return exactlyOne(findNodes(f.node, (n) => n.type === 'VariableDeclarator' &&
    n.init?.type === 'CallExpression' && ['i', 'r'].includes(propertyName(n.init.callee.property)) &&
    n.init.arguments[0]?.value === id), `import ${id}`);
}
const cite = (f, n, label) => ({ ...f.witness(n, label), astType: n.type, text: f.text(n) });

export async function recover(root = APP_ROOT) {
  const corpus = await openCorpus(root);
  const f = {};
  for (const item of EXPECTED) {
    const source = await corpus.factory(item.id, { source: item.source });
    assert.equal(source.provenance.sha256, item.sha256, `review required: changed ${item.label}`);
    f[item.label] = source;
  }
  for (const [id, labels] of [[179736, ['readerA', 'readerB']], [154121, ['identityA', 'identityB', 'identityC', 'identityD']]]) {
    assert.deepEqual(corpus.index.modules.filter((m) => m.ids.includes(id)).map((m) => m.sha256).sort(),
      labels.map((name) => f[name].provenance.sha256).sort(), `all indexed ${id} variants must stay explicit`);
  }
  const readers = ['readerA', 'readerB'].map((label) => {
    const source = f[label];
    const request = exactlyOne(findNodes(source.node, (n) => n.type === 'CallExpression' &&
      n.arguments[0]?.value === 'POST /profiles/verified'), 'used verified read');
    const read = exactlyOne(declarations(source.node).filter((n) => n.type === 'VariableDeclarator' &&
      n.init?.async && n.start < request.start && n.end > request.end), 'direct batch reader').init;
    const safe = exactlyOne(declarations(source.node).filter((n) => n.type === 'VariableDeclarator' &&
      n.init?.async && findNodes(n.init, (n) => n.type === 'CatchClause').length === 1), 'error-to-empty wrapper').init;
    const origin = exactlyOne(declarations(source.node).filter((n) => n.init?.type === 'LogicalExpression' &&
      findNodes(n.init, (n) => n.type === 'StringLiteral' && n.value === 'https://frontend-api-v3.pump.fun').length === 2), 'literal origin in both environment branches');
    const hook = resolve(source, exported(source, 179736, 's'));
    const key = resolve(source, exported(source, 179736, 'B'));
    assert.equal(key.body.type, 'ArrayExpression');
    assert.equal(key.body.elements[0].value, 'user-verified');
    assert.equal(key.body.elements.length, 2);
    assert.equal(literal(objectProperty(request.arguments[1], 'credentials')), 'same-origin');
    assert.deepEqual(request.arguments[1].properties.map((p) => propertyName(p.key)), ['body', 'credentials', 'hooks']);
    assert.deepEqual(objectProperty(request.arguments[1], 'body').properties.map((p) => propertyName(p.key)), ['ids']);
    const query = exactlyOne(findNodes(hook, (n) => n.type === 'ObjectExpression' &&
      n.properties.some((p) => propertyName(p.key) === 'staleTime')), 'actual query defaults');
    assert.deepEqual(query.properties.map((p) => propertyName(p.key)), ['queryKey', 'queryFn', 'enabled', 'staleTime', 'retry']);
    assert.equal(literal(objectProperty(query, 'staleTime')), 1800000);
    assert.equal(literal(objectProperty(query, 'retry')), false);
    assert.ok(findNodes(hook, (n) => n.type === 'NumericLiteral' && n.value === 50).length === 1);
    assert.ok(findNodes(hook, (n) => n.type === 'NumericLiteral' && n.value === 100).length === 2);
    assert.ok(findNodes(hook, (n) => n.type === 'NumericLiteral' && n.value === 10).length === 1);
    const result = exactlyOne(hook.body.body.filter((n) => n.type === 'ReturnStatement'), 'strict returned result');
    assert.equal(result.argument.type, 'BinaryExpression');
    assert.equal(result.argument.operator, '===');
    const nodes = [cite(source, imported(source, 30181), 'actual K-shaped HTTP constructor import'),
      cite(source, origin, 'captured origin; no environment value read'), cite(source, read, 'complete truthy-dedup read and non-ok hook'),
      cite(source, safe, 'complete error-to-empty-map wrapper'), cite(source, key, 'query key; not a credential'),
      cite(source, hook, 'complete per-origin resolver, 50ms/100-key grouping, ten-slot query and strict result')];
    return { factory: source.provenance, sourceNodes: nodes };
  });
  const identities = ['identityA', 'identityB', 'identityC', 'identityD'].map((name) => {
    const source = f[name];
    const hook = resolve(source, exported(source, 154121, 'f'));
    const verifiedImport = imported(source, 179736);
    const lookup = exactlyOne(findNodes(hook, (n) => memberCall(n, verifiedImport.id.name, 's')), 'identity verification call');
    const profileImport = imported(source, 528600);
    const profile = exactlyOne(findNodes(hook, (n) => memberCall(n, profileImport.id.name, 'U')), 'existing profile lookup call');
    const early = exactlyOne(findNodes(hook, (n) => n.type === 'IfStatement' &&
      n.consequent.type === 'ReturnStatement' && n.consequent.argument?.type === 'NullLiteral'), 'absent-address early return');
    assert.ok(lookup.end < early.start, 'verification precedes absent-address return');
    assert.equal(lookup.arguments[0].type, 'ConditionalExpression');
    return { factory: source.provenance, sourceNodes: [cite(source, profileImport, 'accepted profile lookup dependency'),
      cite(source, profile, 'profile-read dependency call; not new recovery'), cite(source, verifiedImport, 'verified reader import'),
      cite(source, lookup, 'enabled userId-nullish-address verification subject'), cite(source, early, 'later absent-address view return'),
      cite(source, hook, 'complete original identity consumer scope; broader presentation not reimplemented')] };
  });
  const renderer = f.renderer;
  const render = resolve(renderer, exported(renderer, 693124, 'S'));
  const verifiedImport = imported(renderer, 179736);
  const lookup = exactlyOne(findNodes(render, (n) => memberCall(n, verifiedImport.id.name, 's')), 'renderer verification call');
  const lookupDeclaration = exactlyOne(findNodes(render, (n) => n.type === 'VariableDeclarator' && n.init === lookup), 'renderer lookup result binding');
  const value = exactlyOne(findNodes(render, (n) => n.type === 'VariableDeclarator' &&
    n.init?.type === 'ConditionalExpression' && n.init.consequent?.name === lookupDeclaration.id.name), 'renderer lookup/direct-prop precedence');
  const badge = exactlyOne(findNodes(render, (n) => n.type === 'ConditionalExpression' && n.test?.name === value.id.name), 'actual badge consumer');
  const chainsImport = imported(renderer, 646908);
  const suppression = exactlyOne(findNodes(render, (n) => n.type === 'AssignmentExpression' &&
    findNodes(n.right, (n) => memberCall(n, chainsImport.id.name, 'B')).length === 1), 'used Near identity suppression expression');
  const rendererNodes = [cite(renderer, verifiedImport, 'actual verified reader import'),
    cite(renderer, lookup, 'verified lookup prop and identity gate'), cite(renderer, suppression, 'complete used display suppression predicate'),
    cite(renderer, value, 'lookup result versus direct verified prop'), cite(renderer, badge, 'actual badge truthiness consumer')];
  const helpers = {};
  for (const [name, id, keys] of [['chains', 646908, ['B', 'R']], ['nearA', 253623, ['D']], ['nearB', 253623, ['D']], ['evm', 605587, ['h']]]) {
    const source = f[name];
    const nodes = keys.map((key) => resolve(source, exported(source, id, key)));
    const regexNames = new Set(nodes.flatMap((node) => findNodes(node, (n) => n.type === 'CallExpression' &&
      n.callee.type === 'MemberExpression' && propertyName(n.callee.property) === 'test' && n.callee.object.type === 'Identifier').map((n) => n.callee.object.name)));
    const regexes = declarations(source.node).filter((n) => n.type === 'VariableDeclarator' && regexNames.has(n.id.name));
    helpers[name] = { factory: source.provenance, sourceNodes: [...nodes.map((n, i) => cite(source, n, `actual ${id}.${keys[i]} gate helper`)),
      ...regexes.map((n) => cite(source, n, 'used regular-expression dependency'))] };
  }
  const route = exactlyOne(findNodes(f.declaration.node, (n) => n.type === 'ObjectProperty' &&
    propertyName(n.key) === 'POST /profiles/verified'), 'existing declaration');
  assert.equal(route.value.arguments[0].value, 'profiles.read');
  const declaredBody = objectProperty(route.value.arguments[1], 'body');
  const declarationNodes = [cite(f.declaration, route, 'existing declared read contract; no new API coverage'),
    cite(f.declaration, resolve(f.declaration, declaredBody), 'existing declared body dependency')];
  const dependencies = {};
  for (const relative of ['reconstruction/profile-lookup/client.mjs', 'reconstruction/profile-lookup/contract.json', 'scripts/original-contracts/source.mjs']) {
    dependencies[relative] = sha256(await readFile(path.join(corpus.root, relative)));
  }
  const implementation = 'reconstruction/verified-profile/client.mjs';
  return {
    schemaVersion: 1, authority: 'Captured source parsed as inert AST; explicit synthetic model capabilities; no captured execution or verification request',
    anchors: corpus.anchors, implementation: { path: implementation, sha256: sha256(await readFile(path.join(corpus.root, implementation))) },
    dependencies, readers, identities,
    renderer: { factory: renderer.provenance, sourceNodes: rendererNodes }, helpers,
    sharedTransport: { sources: [f.websiteConstructor.provenance, f.registry.provenance, f.transport.provenance, f.declaration.provenance],
      sourceNodes: [cite(f.websiteConstructor, resolve(f.websiteConstructor, exported(f.websiteConstructor, 30181, 'K')), 'accepted website HTTP constructor'),
        cite(f.registry, imported(f.registry, 850620), 'declaration included by actual registry'), ...declarationNodes] },
    behavior: {
      capturedOrigin: 'https://frontend-api-v3.pump.fun', operation: 'POST /profiles/verified', credentials: 'same-origin',
      ids: 'Set deduplication then Boolean filtering; empty direct read returns {} without transport; no extra format validation',
      response: 'Raw result; non-ok hook throws; safe wrapper returns {} for every failure',
      resolver: 'Per-origin pending Map; 50ms first-key timer; swap queue/reset timer before asynchronous reads; chunks of100 unique keys; duplicate waiters preserved',
      projection: 'raw response[id] ?? false; chunk catch resolves false; no type/schema repair before hook strict result',
      query: 'user-verified/identifier??empty key; ten-slot memo; (enabled===undefined||enabled)&&!!identifier; stale1800000; retryfalse; other option keys ignored, no final spread',
      result: 'query.data === true only; query context signal ignored; old callbacks capture original identifier',
      identityConsumer: 'enabled ? user?.userId ?? address : undefined; verification call precedes absent-address view return',
      rendererConsumer: 'lookup only for verified===lookup and unsuppressed identity; userId ?? address ?? null; direct verified prop otherwise retained; badge consumes truthiness',
    },
    limits: ['Original badge trust, server eligibility, current provider winner, authentication and authorization are unknown.',
      'No production or loopback POST, credential/session access, React scheduler, mounted UI, backend, wallet, financial or compatibility behavior qualified.',
      'Existing profile lookup, shared transport/declarations and structurally similar user coalescer remain separately credited; no feature milestones change.'],
  };
}
export async function verify(root = APP_ROOT, packet) {
  const expected = Buffer.from(JSON.stringify(await recover(root), null, 2) + '\n');
  const actual = packet ?? await readFile(path.join(root, OUTPUT));
  assert.ok(Buffer.isBuffer(actual) && actual.equals(expected), 'verified-profile contract bytes differ from authenticated output');
  return { readers: 2, identities: 4, renderer: 1 };
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (process.argv.length !== 3 || !['--write', '--check'].includes(mode)) throw Error('Usage: node app/scripts/original-verified-profile.mjs --check|--write');
  if (mode === '--write') await writeFile(path.join(APP_ROOT, OUTPUT), JSON.stringify(await recover(), null, 2) + '\n');
  console.log(await verify());
}
