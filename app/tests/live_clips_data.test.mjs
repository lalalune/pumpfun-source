import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile,writeFile,mkdir,mkdtemp,copyFile,symlink,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {createLiveClipsData} from '../reconstruction/live-clips-data/client.mjs';
import {APP_ROOT,DIRECTORY,recover,verify} from '../reconstruction/live-clips-data/recover.mjs';
const require=createRequire(new URL('../packages/frontend/package.json',import.meta.url));
const React=require('react'),compiler=require('react/compiler-runtime'),{renderToString}=require('react-dom/server');
const kinds={TRENDING_CLIPS:'trending-clips',POPULAR_RECORDINGS:'popular-recordings'};
const listingConstants={LIVE_LISTING_LIMIT:24,LIVE_CARD_COUNTS:{extraSmall:2,small:3,large:4}};
function host({analytics={data:[],isLoading:false},clips={data:[],isLoading:false},coins={data:[],isLoading:false},price={data:2,isLoading:false},body=[],jsonFailure,parseFailure,getFailure,postFailure}={}){
 const calls={events:[],queries:[],coinArgs:[],priceArgs:[],memo:[]},analyticsItemSchema={synthetic:'analytics'},clipItemSchema={synthetic:'clip'};let now=1000;
 class Clock extends Date{constructor(){super(1234567);}static now(){calls.events.push(['now']);return now++;}}
 const client={get(p,o){calls.events.push(['get',p,[...o.searchParams]]);if(getFailure)throw getFailure;return{async json(){calls.events.push(['json','get']);if(jsonFailure)throw jsonFailure;return body;}};},post(p,o){calls.events.push(['post',p,o]);if(postFailure)throw postFailure;return{async json(){calls.events.push(['json','post']);if(jsonFailure)throw jsonFailure;return body;}};}};
 const ports={memoCache:(n)=>{calls.memo.push(n);return compiler.c(n);},useQuery:(o)=>{calls.queries.push(o);return o.queryKey[0]==='vod-analytics'?analytics:clips;},
 useLivestreamApiClient:()=>{calls.events.push(['client']);return client;},useCoinMetadata:o=>{calls.coinArgs.push(o);return coins;},useSolPrice:o=>{calls.priceArgs.push(o);return price;},
 sectionKinds:kinds,listingConstants,Date:Clock,analyticsItemSchema,clipItemSchema,
 arraySchemaModule:{z:{array(s){calls.events.push(['array',s]);return{parse(value){calls.events.push(['parse',s,value]);if(parseFailure)throw parseFailure;return value;}};}}},
 analyticsLogger:{error:(...a)=>calls.events.push(['analytics-error',...a])},clipLogger:{error:(...a)=>calls.events.push(['clip-error',...a])}};
 const flow=createLiveClipsData(ports);function render(props={sectionId:kinds.TRENDING_CLIPS}){let value;function Host(){value=flow.useClipSection(props);return null;}renderToString(React.createElement(Host));return value;}
 return{calls,flow,ports,render,analyticsItemSchema,clipItemSchema};
}
const clip=(room,id,viewCount=0,more={})=>({roomName:room,clipId:id,viewCount,createdAt:'2026-01-01T00:00:00Z',thumbnailUrl:'synthetic-thumbnail',...more});
test('complete E, schemas, two client variants and actual main-page registry/result handoffs authenticate',async()=>{
 const p=await verify();assert.equal(p.factories.length,11);assert.equal(p.schemas.length,6);assert.equal(p.parentEdges.length,3);assert.deepEqual(p.origin.elementPath,['1']);assert.equal(p.fragments.filter(f=>f.label.includes('actual registry')).length,2);assert.equal(p.limits.parserReimplementation,false);assert.ok(p.arrayRuntime.inventoryForwarders.length);
});
test('actual memo/query defaults preserve weekly/monthly mode, floor3limit, oversample5 and no new outer overrides',async()=>{
 const h=host();const out=h.render({sectionId:kinds.TRENDING_CLIPS,initialData:['ignored'],staleTime:0,oversampleFactor:1});assert.deepEqual(h.calls.memo,[10,13,21,12]);
 const [analytics,clips]=h.calls.queries;assert.deepEqual(analytics.queryKey,['vod-analytics','weekly',72,'HIGHLIGHT',5]);assert.deepEqual(clips.queryKey,['clips-by-ids',[]]);assert.equal(analytics.staleTime,3600000);assert.equal(clips.staleTime,3600000);assert.equal('initialData'in analytics,false);
 assert.deepEqual(Object.keys(out),['data','isLoading','fetchNextPage','hasNextPage','isFetchingNextPage']);assert.equal(out.fetchNextPage(),undefined);assert.equal(out.hasNextPage,false);assert.equal(out.isFetchingNextPage,false);
 const monthly=host();monthly.render({sectionId:kinds.POPULAR_RECORDINGS,limit:2.5});assert.deepEqual(monthly.calls.queries[0].queryKey,['vod-analytics','monthly',7,'COMPLETE',5]);
 await analytics.queryFn();assert.deepEqual(h.calls.events.find(x=>x[0]==='get'),['get','vod-analytics/top',[['type','weekly'],['limit','72'],['timestamp','1234'],['oversample','360'],['clipType','HIGHLIGHT']]]);
});
test('analytics JSON precedes exact schema parse; each invocation resamples constructor time without timestamp in key',async()=>{
 const body=[{vodId:'v',roomName:'r',viewsTotal:8}],h=host({body});let time=1999;
 class Clock extends Date{constructor(){super(time);time+=1001;}}
 h.ports.Date=Clock;const flow=createLiveClipsData(h.ports);function Host(){flow.useClipSection({sectionId:kinds.TRENDING_CLIPS});return null;}renderToString(React.createElement(Host));
 const q=h.calls.queries[0];assert.strictEqual(await q.queryFn(),body);assert.strictEqual(await q.queryFn(),body);
 assert.deepEqual(h.calls.events.filter(x=>x[0]==='get').map(x=>Object.fromEntries(x[2]).timestamp),['1','3']);assert.deepEqual(q.queryKey,['vod-analytics','weekly',72,'HIGHLIGHT',5]);
 const e=h.calls.events;assert.ok(e.findIndex(x=>x[0]==='json')<e.findIndex(x=>x[0]==='array'));assert.strictEqual(e.find(x=>x[0]==='parse')[1],h.analyticsItemSchema);assert.strictEqual(e.find(x=>x[0]==='parse')[2],body);
});
test('analytics parser logs and rethrows identity, while transport/JSON failures stay outside parser catch',async()=>{
 for(const failureKind of['getFailure','jsonFailure','parseFailure']){const error=new Error(failureKind),h=host({[failureKind]:error});h.render();await assert.rejects(h.calls.queries[0].queryFn(),e=>e===error);const logged=h.calls.events.filter(e=>e[0]==='analytics-error');assert.equal(logged.length,failureKind==='parseFailure'?1:0);if(logged.length){assert.equal(logged[0][1],'Failed to parse vod analytics');assert.strictEqual(logged[0][2].error,error);}}
});
test('actual ID reducer preserves served duplicates/truthiness; empty clip query still exists and shortcircuits POST/parse',async()=>{
 const h=host();h.render();const before=h.calls.events.length;assert.deepEqual(await h.calls.queries[1].queryFn(),[]);assert.equal(h.calls.events.length,before);
 const data=[{roomName:'A',vodId:'1'},{roomName:'A',vodId:'1'},{roomName:'',vodId:'x'},{roomName:'B',vodId:''},{vodId:'z'},{roomName:'B',vodId:'2'}],body=[clip('A','1')],v=host({analytics:{data,isLoading:false},body});v.render();
 const q=v.calls.queries[1],ids=[{roomName:'A',clipId:'1'},{roomName:'A',clipId:'1'},{roomName:'B',clipId:'2'}];assert.deepEqual(q.queryKey,['clips-by-ids',ids]);assert.strictEqual(await q.queryFn(),body);const post=v.calls.events.find(x=>x[0]==='post');assert.equal(post[1],'clips/by-ids');assert.strictEqual(post[2].json.ids,q.queryKey[1]);assert.strictEqual(v.calls.events.find(x=>x[0]==='parse')[1],v.clipItemSchema);
});
test('clip parse/transport/JSON failures preserve distinct logging boundary and logger throw is not swallowed',async()=>{
 for(const failureKind of['postFailure','jsonFailure','parseFailure']){const error=new Error(failureKind),h=host({analytics:{data:[{roomName:'A',vodId:'1'}]},[failureKind]:error});h.render();await assert.rejects(h.calls.queries[1].queryFn(),e=>e===error);const logged=h.calls.events.filter(e=>e[0]==='clip-error');assert.equal(logged.length,failureKind==='parseFailure'?1:0);if(logged.length)assert.equal(logged[0][1],'[useClipsByIds] Failed to parse clips');}
 const first=new Error('parser'),second=new Error('logger'),h=host({parseFailure:first});h.ports.analyticsLogger.error=()=>{throw second;};h.render();await assert.rejects(h.calls.queries[0].queryFn(),e=>e===second);
});
test('view-count sort, retained-entry room spacing and original-index restoration do not cap nominal output',()=>{
 const data=['A','A','A','B','C','D','A','E'].map((r,i)=>clip(r,String(i),100-i)),h=host({clips:{data,isLoading:false}}),out=h.render({sectionId:kinds.TRENDING_CLIPS,limit:1});
 assert.deepEqual(out.data.map(c=>c.id),['0','3','4','5','6','7']);assert.deepEqual(h.calls.coinArgs[0],{mints:['A','B','C','D','E']});assert.equal(data.length,8);assert.equal(data[0].clipId,'0');assert.equal(out.data.length,6);
 const unsorted=[clip('x','x',null),clip('b','b',4),clip('a','a',4),clip('z','z',-1)],v=host({clips:{data:unsorted,isLoading:false}});assert.deepEqual(v.render().data.map(c=>c.id),['b','a','x','z']);
});
test('full cards preserve raw coin identity, last metadata, truthiness/playlist fallbacks and separate epoch-zero/invalid clock samples',()=>{
 const old={mint:'A',name:'old'},coin={mint:'A',name:'Coin A',creator:'author',username:'',market_cap:7,image_uri:'',is_currently_live:1,playlist_url_low:'coin-low',playlist_url:'coin-full',created_timestamp:42,symbol:'AA'};
 const data=[clip('A','a',5,{createdAt:'1970-01-01T00:00:00Z',title:'',playlistUrl:'',mp4Url:'clip-mp4',hidden:true,deletionStatus:'HARD_DELETED'}),clip('B','b',4,{createdAt:'invalid',title:'Explicit'}),clip('C','c',3,{playlistUrl:'clip-playlist'})];
 const h=host({clips:{data,isLoading:false},coins:{data:[old,coin],isLoading:false}}),out=h.render();const a=out.data[0];assert.strictEqual(a.coin,coin);assert.equal(a.title,'Coin A');assert.equal(a.marketCap,14);assert.deepEqual(a.creator,{address:'author',username:undefined});assert.equal(a.playlistUrl,'clip-mp4');assert.equal(a.isLive,1);assert.equal(a.thumbnailUpdatedAt,1000);assert.equal(a.coinCreatedTimestamp,42);assert.equal(a.viewerCountLabel,'views');assert.equal(a.linkUrl,'/coin/A?clip=a');assert.equal(a.thumbnail,a.ipfsThumbnail);
 const b=out.data[1];assert.equal(b.title,'Explicit');assert.equal(b.thumbnailUpdatedAt,1001);assert.equal(b.avatarUri,'');assert.equal(b.coinCreatedTimestamp,null);assert.equal(b.marketCap,null);assert.equal(b.playlistUrl,undefined);assert.deepEqual(b.creator,{address:undefined,username:undefined});assert.equal(out.data[2].playlistUrl,'clip-playlist');
 const zero=host({clips:{data:[clip('A','z',0)],isLoading:false},coins:{data:[coin],isLoading:false},price:{data:0,isLoading:true,isError:true}});assert.equal(zero.render().data[0].marketCap,null);
 const fallback=host({clips:{data:[clip('A','f')],isLoading:false},coins:{data:[coin],isLoading:false}});assert.equal(fallback.render().data[0].playlistUrl,'coin-low');
});
test('loading only joins analytics/clips/coin and does not manufacture error, next-page or SOLprice states',()=>{
 for(const key of['analytics','clips','coins']){const h=host({[key]:{data:[],isLoading:true}});assert.equal(h.render().isLoading,true);}
 const h=host({analytics:{data:[],isLoading:false,isError:true},clips:{data:[],isLoading:false,error:Error('external')},coins:{data:[],isLoading:false},price:{data:undefined,isLoading:true,isError:true}});const out=h.render();assert.equal(out.isLoading,false);assert.equal('error'in out,false);assert.equal('isError'in out,false);
});
test('capability admission requires original schema/query/read/date contracts without invoking them',()=>{
 const h=host();for(const key of['memoCache','useQuery','useLivestreamApiClient','useCoinMetadata','useSolPrice','Date','analyticsItemSchema','clipItemSchema','arraySchemaModule','listingConstants'])assert.throws(()=>createLiveClipsData({...h.ports,[key]:undefined}),TypeError);assert.deepEqual(h.calls.events,[]);
});
async function exportInputs(t){const {proof}=await recover(),root=await mkdtemp(path.join(os.tmpdir(),'public clips VOD replay '));t.after(()=>rm(root,{recursive:true,force:true}));const files=[DIRECTORY+'/recover.mjs',DIRECTORY+'/client.mjs',DIRECTORY+'/PROVENANCE.json','scripts/original-contracts/source.mjs','scripts/settings-client-contract.mjs','evidence/web/manifest.json','recovered/modules.json',proof.origin.capture.source,...proof.factories.map(f=>f.source)];for(const file of new Set(files)){const p=path.join(root,file);await mkdir(path.dirname(p),{recursive:true});await copyFile(path.join(APP_ROOT,file),p);}await symlink(path.join(APP_ROOT,'node_modules'),path.join(root,'node_modules'),'dir');return root;}
test('source replay is portable from explicit public inputs and rejects altered spacing/card operations',async t=>{
 const root=await exportInputs(t);await verify(root);const file=path.join(root,DIRECTORY,'client.mjs'),source=await readFile(file,'utf8');assert.ok(source.includes('l.g.large'));await writeFile(file,source.replace('l.g.large','l.g.small'));await assert.rejects(verify(root),/complete clips\/VOD source differs/);
});
