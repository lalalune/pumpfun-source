// Read captured ASTs as data; never evaluate/import a captured module.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from '@babel/generator';
import { openCorpus, findNodes, exactlyOne, sha256 } from './original-contracts/source.mjs';
const app = fileURLToPath(new URL('..', import.meta.url));
export const outputPath = 'reconstruction/contract-client/contract.json';
const pin = '9015e4bad4b1f0bb4b245e446689d9b7e939b3ba922044c82dcd9e8d5f3d9ed5';
const require = (value, message) => { if (!value) throw Error(message); };
export async function recover(root = app) {
  const corpus = await openCorpus(root);
  const variants = corpus.index.modules.filter(row => row.ids.includes(898661));
  require(variants.length === 1 && variants[0].sha256 === pin, 'review changed request compiler variants');
  const owner = await corpus.factory(898661, { source: variants[0].origins[0].source });
  const assignment = exactlyOne(findNodes(owner.node, node => node.type === 'AssignmentExpression' &&
    node.left.type === 'MemberExpression' && node.left.object.name === 'r' &&
    node.left.property.name === 'createContractClient' && node.right.type === 'ArrowFunctionExpression'), 'complete client owner');
  const imports = findNodes(owner.node, node => node.type === 'VariableDeclarator' &&
    node.init?.type === 'CallExpression' && node.init.callee?.object?.name === owner.runtime &&
    node.init.callee?.property?.name === 'r').map(node => ({
      id: node.init.arguments[0].value, local: node.id.name,
      evidence: owner.witness(node, 'actual imported dependency'),
    }));
  require(JSON.stringify(imports.map(row => row.id)) === JSON.stringify([858694,402030,233815,4171]), 'compiler dependency closure changed');
  const source = node => ({syntax:generate(node,{compact:true,comments:false}).code,
    evidence:owner.witness(node,'original complete request compiler')});
  return { schemaVersion:1, classification:'Complete request compilation owner, injected transport/catalog; no native server or compatibility claim',
    anchors:corpus.anchors, owner:owner.provenance, occurrences:variants[0].origins,
    imports, implementation:source(assignment), fullFactory:source(owner.node),
    maintainedSha256:sha256(await readFile(path.join(root,'reconstruction/contract-client/client.mjs'))),
    creditedPrerequisite:{path:'reconstruction/contract-http-errors/decode.mjs',
      sha256:sha256(await readFile(path.join(root,'reconstruction/contract-http-errors/decode.mjs'))),
      newlyRecovered:false},
    boundaries:['Transport, route catalog and safeParse implementations are explicit required ports.',
      'Query/multipart preflight precedes HTTP error normalization; successful JSON is not response-schema validated.',
      'Native FormData constructor is an explicit platform port; tests do not qualify a React Native runtime.',
      'No original captured code executes, no default production transport, auth, provider or network is created.'] };
}
export async function verify(root = app) {
  const text=JSON.stringify(await recover(root),null,2)+'\n';
  require(await readFile(path.join(root,outputPath),'utf8')===text,'saved request compiler contract differs');
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const args=process.argv.slice(2);require(args.length===1 && ['--write','--check'].includes(args[0]),'use --write or --check');
  if(args[0]==='--write'){await mkdir(path.dirname(path.join(app,outputPath)),{recursive:true});await writeFile(path.join(app,outputPath),JSON.stringify(await recover(),null,2)+'\n');}
  await verify();console.log('Verified complete 898661 request compiler, source bindings and credited decoder; captured code executed: false');
}
