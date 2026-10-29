import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { openCorpus, exactlyOne, findNodes, objectProperty, literal, member } from './source.mjs';
import { createSchemaExtractor } from './schema.mjs';

const pins = {
  manifestSha256: '9e0fc00719eb8c919dd4205d3c118eb48c4927e056c77e8343e26d6f7189bbb5',
  inventorySha256: '1d268ae7f2eb0f61eaaffd222269bf29d9ce06e9946372861721b2f159d868e2',
};
const operation = 'GET /fees/holder-rewards';
const contractChunk = 'evidence/web/objects/2b47dd0b38a1608f.js';

export async function extractHolderRewards(root) {
  const corpus = await openCorpus(root);
  for (const [name, expected] of Object.entries(pins)) if (corpus.anchors[name] !== expected) throw new Error(`unreviewed holder-rewards input: ${name}`);
  const fragments = new Map();
  const factories = new Map();
  const add = (factory, node, label) => {
    const witness = factory.witness(node, label);
    const key = `${witness.source}:${witness.utf16.join(':')}`;
    fragments.set(key, { ...witness, text: factory.text(node) });
    return key;
  };
  const factory = async (id) => {
    const value = await corpus.factory(id);
    factories.set(`${id}:${value.provenance.source}`, value.provenance);
    return value;
  };

  const extractor = createSchemaExtractor(corpus);
  const declared = await extractor.declaration(698550, 'feesRoutes');
  factories.set(`698550:${declared.factory.provenance.source}`, declared.factory.provenance);
  const route = objectProperty(declared.node.arguments[0], operation);
  // A bare route object: no publicRead wrapper declares a developer scope here.
  if (route?.type !== 'ObjectExpression') throw new Error('holder-rewards route shape changed');
  const declaration = add(declared.factory, route, 'holder-rewards route declaration');
  const query = await extractor.compile(objectProperty(route, 'query'), declared.factory);
  const response = await extractor.compile(objectProperty(route, 'response'), declared.factory);
  const declarations = extractor.document({ 'x-holder-rewards-query': query, 'x-holder-rewards-response': response });
  for (const witness of extractor.witnesses()) {
    const key = `${witness.source}:${witness.utf16.join(':')}`;
    const capture = await corpus.capture(witness.source);
    fragments.set(key, { ...witness, ...(!witness.label.startsWith('factory ') ? { text: capture.text.slice(...witness.utf16) } : {}) });
  }

  // Reachability: every authenticated JS capture is searched for the literal.
  const occurrences = [];
  for (const record of corpus.manifest.records) {
    if (record.status !== 200 || !/^evidence\/web\/objects\//.test(record.path) || !new URL(record.url).pathname.endsWith('.js')) continue;
    const { text } = await corpus.capture(record.path);
    if (text.includes(`"${operation}"`)) occurrences.push(record.path);
  }
  if (occurrences.length !== 1 || occurrences[0] !== contractChunk) throw new Error('holder-rewards reachability changed; review captured callers');

  // Sibling fee reads in 99415 use the website client; holder-rewards is not among them.
  const reads = await factory(99415);
  const clientImport = exactlyOne(findNodes(reads.node, (node) => node.type === 'VariableDeclarator' &&
    node.init?.type === 'CallExpression' && member(node.init.callee, reads.runtime, 'i') && node.init.arguments[0]?.value === 759257), 'fee reads client import');
  const client = exactlyOne(findNodes(reads.node, (node) => node.type === 'CallExpression' &&
    node.callee.type === 'SequenceExpression' && member(node.callee.expressions[1], clientImport.id.name, 'j')), 'fee reads client.j');
  const siblingReads = [...new Set(findNodes(reads.node, (node) => node.type === 'StringLiteral' && node.value.startsWith('GET /fees/')).map((node) => node.value))].sort();
  if (siblingReads.includes(operation)) throw new Error('fee reads now call holder-rewards; bind its caller instead');
  const origins = await factory(503630);
  const origin = exactlyOne(findNodes(origins.node, (node) => node.type === 'ArrowFunctionExpression' &&
    node.body.type === 'StringLiteral' && node.body.value === 'https://frontend-api-v3.pump.fun'), 'website origin');

  return { formatVersion: 1, operation, authority: 'Original captured declaration AST; no captured JavaScript evaluated',
    frozenInputs: corpus.anchors, summary: literal(objectProperty(route, 'summary')), declaration, declarations,
    reachability: { occurrences, capturedCallers: 0,
      disposition: 'Only the declaration names this operation. Its caller, service origin and authorization are not observed' },
    siblingTransport: { factory: 99415, reads: siblingReads,
      clientImport: add(reads, clientImport.init, 'fee reads import website client'),
      clientCall: add(reads, client, 'fee reads construct client.j'),
      origin: add(origins, origin, 'website origin R'),
      disposition: 'Context only: the sibling fee reads use 759257.j at https://frontend-api-v3.pump.fun; this does not bind holder-rewards to that origin' },
    factories: [...factories.values()], fragments: [...fragments.values()],
    exclusions: ['No upstream request, response fixture, server behavior or compatibility claim',
      'Cursor mode, price marks, sort definitions, tie order and book folding are described, not observed',
      'No captured Zod runtime is executed; coercion, defaults and stripping are not reconstructed'] };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [mode] = process.argv.slice(2);
  if (process.argv.length !== 3 || !['--write', '--check'].includes(mode)) throw new Error('usage: holder-rewards.mjs --write|--check');
  const root = fileURLToPath(new URL('../..', import.meta.url));
  const destination = path.join(root, 'contracts/original-holder-rewards.json');
  const result = `${JSON.stringify(await extractHolderRewards(root), null, 2)}\n`;
  if (mode === '--check') {
    if (await fs.readFile(destination, 'utf8') !== result) throw new Error('holder-rewards declaration artifact changed');
  } else {
    const staging = await fs.mkdtemp(path.join(path.dirname(destination), '.holder-rewards-'));
    try { await fs.writeFile(path.join(staging, 'artifact.json'), result); await fs.rename(path.join(staging, 'artifact.json'), destination); }
    finally { await fs.rm(staging, { recursive: true, force: true }); }
  }
  console.log(`${mode === '--check' ? 'Verified' : 'Wrote'} original holder-rewards declaration`);
}
