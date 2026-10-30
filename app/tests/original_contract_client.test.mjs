import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import { readFile,writeFile,mkdir,mkdtemp,copyFile,rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createContractClient } from '../reconstruction/contract-client/client.mjs';
import { ContractError } from '../reconstruction/contract-http-errors/decode.mjs';
import { recover,verify,outputPath } from '../scripts/original-contract-client.mjs';
const root=fileURLToPath(new URL('..',import.meta.url));
const miss={safeParse:()=>({success:false})};
const ports=(contracts={})=>({contracts,routeErrorSchema:()=>true,contractErrorBody:miss});
async function server(t){
 const requests=[];
 const app=createServer(async(req,res)=>{
  const chunks=[];for await(const chunk of req)chunks.push(chunk);
  const body=Buffer.concat(chunks).toString('utf8');
  const result={url:req.url,method:req.method,contentType:req.headers['content-type'],body};requests.push(result);
  res.setHeader('content-type','application/json');
  if(req.url.startsWith('/deny')){res.statusCode=400;res.end(JSON.stringify({error:'BAD_REQUEST',message:['denied',7,'reason']}));}
  else res.end(JSON.stringify(result));
 });app.listen(0,'127.0.0.1');await once(app,'listening');t.after(()=>new Promise(resolve=>{app.closeAllConnections();app.close(resolve);}));
 const base=`http://127.0.0.1:${app.address().port}/`;
 const transport=(relative,options)=>({async json(){
  const url=new URL(relative,base);if(options.searchParams)url.search=new URLSearchParams(options.searchParams).toString();
  const headers={...options.headers};let body=options.body;
  if(Object.hasOwn(options,'json')){body=JSON.stringify(options.json);headers['content-type']='application/json';}
  const response=await fetch(url,{...options,headers,body});
  if(!response.ok){const error=Error('local HTTP failure');error.response=response;throw error;}
  return response.json();
 }});
 return{requests,transport};
}
test('complete owner is authenticated and generated output is current',async()=>{
 await verify(root);const contract=await recover(root);
 assert.equal(contract.owner.id,898661);assert.deepEqual(contract.imports.map(row=>row.id),[858694,402030,233815,4171]);
 for(const marker of ['split(" ",2)','multipartFiles','FormData','safeParse','encodeURIComponent','...m'])assert.ok(contract.fullFactory.syntax.includes(marker),marker);
 assert.equal(contract.creditedPrerequisite.newlyRecovered,false);
});
test('real loopback GET: path encoding, array/scalar wire query and successful response',async(t)=>{
 const {transport}=await server(t);const call=createContractClient(transport,ports());
 const result=await call('GET /items/{id}',{params:{id:'a/b ?'},query:{many:[1,true],nil:null,skip:undefined}});
 assert.equal(result.url,'/items/a%2Fb%20%3F?many=1%2Ctrue&nil=null');assert.equal(result.method,'GET');
 assert.equal((await call('GET /items/{id}')).url,'/items/undefined');
 await assert.rejects(call('GET /items/{id}',{params:null}),TypeError);
});
test('real loopback multipart keeps Blob bytes, serializes JSON fields and skips absent file parts',async(t)=>{
 const {transport}=await server(t);const call=createContractClient(transport,ports({'POST /upload':{multipart:true,multipartFiles:['image','other']}}));
 const result=await call('POST /upload',{body:{image:new Blob(['original synthetic bytes'],{type:'text/plain'}),other:null,config:{x:1},flag:false,skip:undefined}});
 assert.match(result.contentType,/^multipart\/form-data; boundary=/);assert.match(result.body,/original synthetic bytes/);
 assert.match(result.body,/{"x":1}/);assert.match(result.body,/false/);assert.doesNotMatch(result.body,/name="other"|name="skip"/);
});
test('no selected non-null file means ordinary JSON; trailing transport options override defaults',async(t)=>{
 const {transport}=await server(t);const call=createContractClient(transport,ports({'POST /upload':{multipart:true}}));
 const json=await call('POST /upload',{body:{image:null,name:'row'}});assert.equal(json.contentType,'application/json');assert.equal(json.body,'{"image":null,"name":"row"}');
 const override=await call('GET /items/{id}',{params:{id:'x'},query:{old:'ignored'},method:'post',searchParams:{new:'value'},json:{different:true}});
 assert.equal(override.method,'POST');assert.equal(override.url,'/items/x?new=value');assert.equal(override.body,'{"different":true}');
});
test('optional empty-array query invokes actual schema port; invalid preflight never calls transport',async()=>{
 let calls=0,parses=0;const transport=()=>{calls++;return{json:async()=>true};};
 const config=ports({'GET /list':{query:{shape:{optional:{safeParse(value){parses++;assert.equal(value,undefined);return{success:true};}}}}}});
 const call=createContractClient(transport,config);assert.equal(await call('GET /list',{query:{optional:[]}}),true);assert.equal(parses,1);
 await assert.rejects(call('GET /list',{query:{required:[]}}),/requires at least one item/);
 await assert.rejects(call('GET /list',{query:{items:['a,b']}}),/contains a comma/);assert.equal(calls,1);
});
test('browser rejects descriptors/handbuilt FormData; native platform branch accepts descriptors and rejects Blob',async()=>{
 const calls=[];const transport=(_path,options)=>{calls.push(options);return{json:async()=>true};};
 const config=ports({'POST /upload':{multipart:true}}),browser=createContractClient(transport,config);
 const descriptor={uri:'file:///synthetic',name:'local.txt',type:'text/plain'};
 await assert.rejects(browser('POST /upload',{body:{image:descriptor}}),/only React Native/);
 await assert.rejects(browser('POST /upload',{body:new FormData()}),/hand-built FormData/);
 await assert.rejects(browser('POST /upload',{body:{image:4}}),/neither a Blob/);
 class NativeFormData{parts=[];getParts(){return this.parts;}append(...part){this.parts.push(part);}}
 const native=createContractClient(transport,{...config,FormDataType:NativeFormData});
 await native('POST /upload',{body:{image:descriptor,meta:null}});assert.deepEqual(calls[0].body.parts,[['image',descriptor],['meta','null']]);
 await assert.rejects(native('POST /upload',{body:{image:new Blob(['x'])}}),/React Native's FormData cannot send/);
});
test('real HTTP error uses credited decoder; ordinary transport/parse failures retain identity',async(t)=>{
 const {transport}=await server(t);const call=createContractClient(transport,ports());
 await assert.rejects(call('GET /deny'),error=>error instanceof ContractError && error.status===400 && error.serverMessage==='denied; reason' && error.body.error==='BAD_REQUEST');
 for(const original of [new DOMException('local','AbortError'),new SyntaxError('local JSON')]){
  const failing=createContractClient(()=>({json:async()=>{throw original;}}),ports());
  await assert.rejects(failing('GET /path'),error=>error===original);
 }
});
test('changed maintained output and changed captured bytes fail the source gate',async(t)=>{
 const temporary=await mkdtemp(path.join(tmpdir(),'contract-compiler-'));t.after(()=>rm(temporary,{recursive:true,force:true}));
 const saved=await recover(root);
 for(const relative of ['evidence/web/manifest.json','recovered/modules.json',saved.owner.source,'reconstruction/contract-client/client.mjs','reconstruction/contract-http-errors/decode.mjs',outputPath]){
  await mkdir(path.dirname(path.join(temporary,relative)),{recursive:true});await copyFile(path.join(root,relative),path.join(temporary,relative));
 }
 await verify(temporary);
 await writeFile(path.join(temporary,'reconstruction/contract-client/client.mjs'),'changed');await assert.rejects(verify(temporary),/saved request compiler contract differs/);
 await copyFile(path.join(root,'reconstruction/contract-client/client.mjs'),path.join(temporary,'reconstruction/contract-client/client.mjs'));
 await writeFile(path.join(temporary,saved.owner.source),(await readFile(path.join(temporary,saved.owner.source),'utf8'))+'\n// changed');
 await assert.rejects(verify(temporary),/capture authentication failed/);
});
