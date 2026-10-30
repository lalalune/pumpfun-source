import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {once} from 'node:events';
import {mkdtemp,mkdir,copyFile,writeFile,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {walletMappingClient,walletMappingKey} from '../reconstruction/wallet-mapping/client.mjs';
import {UserFetchError} from '../reconstruction/profile-lookup/client.mjs';
import {recover,verify,outputPath} from '../scripts/original-wallet-mapping.mjs';
const root=fileURLToPath(new URL('..',import.meta.url));
const address=i=>i.toString(2).replace(/[01]/g,bit=>bit==='0'?'3':'2').padStart(32,'1');
async function fixture(t){
 const requests=[],users=new Map();let failBatch=false;
 const app=createServer(async(req,res)=>{
  const chunks=[];for await(const chunk of req)chunks.push(chunk);const text=Buffer.concat(chunks).toString();
  requests.push({method:req.method,url:req.url,body:text});res.setHeader('content-type','application/json');
  if(req.url==='/users/batch'){
   if(failBatch){res.statusCode=503;res.end('{"error":"unavailable"}');return;}
   res.end(JSON.stringify(JSON.parse(text).addresses.flatMap(id=>users.has(id)?[users.get(id)]:[])));return;
  }
  const id=decodeURIComponent(req.url.slice('/users/'.length));
  if(!users.has(id)){res.statusCode=404;res.end('{}');}else res.end(JSON.stringify(users.get(id)));
 });app.listen(0,'127.0.0.1');await once(app,'listening');t.after(()=>new Promise(resolve=>{app.closeAllConnections();app.close(resolve);}));
 const origin=`http://127.0.0.1:${app.address().port}`;
 const request=async(operation,options)=>{
  const [method,template]=operation.split(' ');const relative=template.replace('{id}',encodeURIComponent(String(options.params?.id)));
  const response=await fetch(origin+relative,{method,headers:options.headers,signal:options.signal,body:options.body===undefined?undefined:JSON.stringify(options.body)});
  for(const hook of options.hooks?.afterResponse??[])await hook(undefined,options,response);
  const text=await response.text();return options.parseJson?options.parseJson(text):JSON.parse(text);
 };
 let time=1000000;const client=walletMappingClient({request,createClient:({clientServerUrl})=>{assert.equal(clientServerUrl,origin);return request;},getOrigin:()=>origin,now:()=>time});
 const states=new Map(),writes=[];
 const cache={getQueryState:key=>states.get(JSON.stringify(key)),setQueryData(key,data){states.set(JSON.stringify(key),{data,dataUpdatedAt:time});writes.push({key,data});}};
 return{client,requests,users,states,writes,cache,setTime:value=>time=value,failBatch:()=>failBatch=true};
}
test('complete source owner, four exports and actual caller are authenticated',async()=>{
 await verify(root);const value=await recover(root);assert.equal(value.owner.id,795663);
 assert.equal(value.caller.provenance.id,689943);assert.equal(value.prerequisites.length,2);
 assert.ok(value.prerequisites.every(row=>!row.newlyRecovered));
});
test('real HTTP single read returns mapping/null and preserves typed not-found behavior',async(t)=>{
 const f=await fixture(t),a=address(1),b=address(2);f.users.set(a,{address:a,canonical_evm_wallet:'0x123'});f.users.set(b,{address:b});
 assert.equal(await f.client.single({solAddress:a}),'0x123');assert.equal(await f.client.single({solAddress:b}),null);
 assert.equal(await f.client.single({solAddress:address(3)}),null);assert.equal(f.requests.length,3);
});
test('batch deduplicates before concurrent 100-key reads, preserves missing rows and sends no empty request',async(t)=>{
 const f=await fixture(t),ids=Array.from({length:205},(_,i)=>address(i+1));
 ids.forEach((id,i)=>{if(i%2===0)f.users.set(id,{address:id,canonical_evm_wallet:`evm-${i}`});});
 const result=await f.client.batch({solAddresses:[...ids,ids[0],ids[1]]});
 assert.equal(Object.keys(result).length,205);assert.equal(result[ids[0]],'evm-0');assert.equal(result[ids[1]],null);
 assert.deepEqual(f.requests.map(row=>JSON.parse(row.body).addresses.length),[100,100,5]);
 assert.deepEqual(await f.client.batch({solAddresses:[]}),{});assert.equal(f.requests.length,3);
});
test('cache keeps strings indefinitely, reuses null strictly below five minutes, refetches at boundary',async(t)=>{
 const f=await fixture(t),a=address(1),b=address(2),c=address(3),d=address(4);
 f.states.set(JSON.stringify(walletMappingKey(a)),{data:'permanent',dataUpdatedAt:0});
 f.states.set(JSON.stringify(walletMappingKey(b)),{data:null,dataUpdatedAt:700001});
 f.states.set(JSON.stringify(walletMappingKey(c)),{data:null,dataUpdatedAt:700000});
 f.users.set(c,{address:c,canonical_evm_wallet:'new-c'});
 const result=await f.client.cached({solAddresses:[a,b,c,d,a],queryClient:f.cache});
 assert.deepEqual(result,{[a]:'permanent',[b]:null,[c]:'new-c',[d]:null});
 assert.deepEqual(JSON.parse(f.requests[0].body).addresses,[c,d]);assert.equal(f.writes.length,2);
 await f.client.cached({solAddresses:[d,c],queryClient:f.cache});assert.equal(f.requests.length,1);
 f.setTime(1300000);await f.client.cached({solAddresses:[d],queryClient:f.cache});assert.equal(f.requests.length,2);
});
test('failed batch rejects cache refresh without writes; signal cancellation is forwarded',async(t)=>{
 const f=await fixture(t);f.failBatch();
 await assert.rejects(f.client.cached({solAddresses:[address(1)],queryClient:f.cache}),error=>error instanceof UserFetchError && error.status===503);
 assert.deepEqual(f.writes,[]);
 const controller=new AbortController();controller.abort();
 await assert.rejects(f.client.single({solAddress:address(2),signal:controller.signal}),error=>error.name==='AbortError');
});
test('query owner preserves admission, fresh options, null key and host result',async(t)=>{
 const f=await fixture(t),a=address(1);f.users.set(a,{address:a,canonical_evm_wallet:'evm'});
 const normal=f.client.queryOptions({solAddress:a});assert.equal(normal.enabled,true);assert.equal(normal.staleTime,300000);assert.ok(!Object.hasOwn(normal,'refetchOnWindowFocus'));
 const fresh=f.client.queryOptions({solAddress:a,fresh:true,enabled:false});assert.equal(fresh.enabled,false);assert.equal(fresh.staleTime,0);assert.equal(fresh.refetchOnWindowFocus,false);
 const absent=f.client.queryOptions({});assert.deepEqual(absent.queryKey,walletMappingKey(null));assert.equal(absent.enabled,false);
 const signal=new AbortController().signal;assert.equal(await normal.queryFn({signal}),'evm');
 const result={data:'local-host-result'};assert.equal(f.client.useWalletMapping(options=>{assert.deepEqual(options.queryKey,walletMappingKey(a));return result;},{solAddress:a}),result);
});
test('source gate tolerates prerequisite checkout line endings and rejects changed implementation/capture',async(t)=>{
 const temporary=await mkdtemp(path.join(tmpdir(),'mapping-owner-'));t.after(()=>rm(temporary,{recursive:true,force:true}));const saved=await recover(root);
 for(const relative of ['evidence/web/manifest.json','recovered/modules.json',saved.owner.source,'reconstruction/wallet-mapping/client.mjs',...saved.prerequisites.map(row=>row.path),outputPath]){
  await mkdir(path.dirname(path.join(temporary,relative)),{recursive:true});await copyFile(path.join(root,relative),path.join(temporary,relative));
 }
 await verify(temporary);for(const row of saved.prerequisites){const file=path.join(temporary,row.path);await writeFile(file,(await readFile(file,'utf8')).replace(/\r\n/g,'\n'));}
 const inventory=path.join(temporary,'recovered/modules.json');await writeFile(inventory,(await readFile(inventory,'utf8')).replace(/\r\n/g,'\n').replace(/\n/g,'\r\n'));await verify(temporary);
 await writeFile(path.join(temporary,'reconstruction/wallet-mapping/client.mjs'),'changed');await assert.rejects(verify(temporary),/source binding differs/);
 await copyFile(path.join(root,'reconstruction/wallet-mapping/client.mjs'),path.join(temporary,'reconstruction/wallet-mapping/client.mjs'));
 await writeFile(path.join(temporary,saved.owner.source),'changed capture');await assert.rejects(verify(temporary),/capture authentication failed/);
});
