import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generate} from '@babel/generator';
import {openCorpus,findNodes,exactlyOne,sha256} from './original-contracts/source.mjs';
const rootDefault=fileURLToPath(new URL('..',import.meta.url));
export const outputPath='reconstruction/wallet-mapping/contract.json';
const pins={795663:'11dbd34fa7c445a0bad7970b695619d27c2c16a9242ad1e6c37d2e1269e912cc',689943:'2f14d3455aeb9f4d16ae197ae4f9ca0ca62d74422f0c816b5776336c96644f6e'};
const check=(ok,message)=>{if(!ok)throw Error(message);};
export async function recover(root=rootDefault){
 const corpus=await openCorpus(root),selected={};
 for(const [id,pin] of Object.entries(pins)){
  const rows=corpus.index.modules.filter(row=>row.ids.includes(Number(id)));
  check(rows.length===1 && rows[0].sha256===pin,`review changed wallet mapping owner/caller ${id}`);
  selected[id]=await corpus.factory(Number(id),{source:rows[0].origins[0].source});
 }
 const owner=selected[795663],caller=selected[689943];
 const exports=exactlyOne(findNodes(owner.node,node=>node.type==='CallExpression' && node.callee?.object?.name===owner.runtime && node.callee.property?.name==='s'),'mapping exports');
 check(JSON.stringify(exports.arguments[0].elements.filter((_,index)=>index%3===0).map(node=>node.value))===JSON.stringify(['a','i','m','O']),'complete four mapping exports');
 const dependency=exactlyOne(findNodes(caller.node,node=>node.type==='VariableDeclarator' && node.init?.type==='CallExpression' && node.init.arguments[0]?.value===795663),'actual mapping caller import');
 const imports=findNodes(owner.node,node=>node.type==='VariableDeclarator' && node.init?.type==='CallExpression' && node.init.callee?.object?.name===owner.runtime).map(node=>node.init.arguments[0]?.value);
 check(JSON.stringify(imports)===JSON.stringify([445242,528600,690877,544930,503630]),'mapping import closure changed');
 const prerequisites=[];
 for(const relative of ['reconstruction/profile-lookup/client.mjs','reconstruction/user-batch/client.mjs'])prerequisites.push({path:relative,
  canonicalLfSha256:sha256(Buffer.from((await readFile(path.join(root,relative),'utf8')).replace(/\r\n/g,'\n'))),newlyRecovered:false});
 return{schemaVersion:1,classification:'Complete selected SOL-to-EVM mapping read/cache/query owner, required transport and query ports; no identity inference or native API claim',
  anchors:{manifestSha256:corpus.anchors.manifestSha256,
   inventoryCanonicalLfSha256:sha256(Buffer.from((await readFile(path.join(root,'recovered/modules.json'),'utf8')).replace(/\r\n/g,'\n')))},owner:owner.provenance,occurrences:corpus.index.modules.find(row=>row.ids.includes(795663)).origins,
  fullOwner:{syntax:generate(owner.node,{compact:true,comments:false}).code,evidence:owner.witness(owner.node,'complete original wallet mapping owner')},
  exports:owner.witness(exports,'four actual mapping exports'),imports,
  caller:{provenance:caller.provenance,evidence:caller.witness(dependency,'actual owner import; not a rendered-reachability or active-provider claim')},
  maintainedSha256:sha256(await readFile(path.join(root,'reconstruction/wallet-mapping/client.mjs'))),prerequisites,
  boundaries:['Only supplied local identifiers/facts are used in tests; no wallet discovery, credential, session, provider or default production request.',
   'Credited source hashes normalize checkout CRLF to LF; raw captured bytes remain strict.',
   'The host supplies actual useQuery/cache scheduling and schema/transport behavior. Compiler memo identity and arbitrary React interleavings are not qualified.']};
}
export async function verify(root=rootDefault){check(await readFile(path.join(root,outputPath),'utf8')===JSON.stringify(await recover(root),null,2)+'\n','saved mapping source binding differs');}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const args=process.argv.slice(2);check(args.length===1&&['--write','--check'].includes(args[0]),'use --write or --check');
 if(args[0]==='--write'){await mkdir(path.dirname(path.join(rootDefault,outputPath)),{recursive:true});await writeFile(path.join(rootDefault,outputPath),JSON.stringify(await recover(),null,2)+'\n');}
 await verify();console.log('Verified complete 795663 mapping owner, caller and credited prerequisites; captured code executed: false');
}
