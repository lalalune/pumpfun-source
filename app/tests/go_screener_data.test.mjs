import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtemp, mkdir, copyFile, readFile, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { buildBountyFilters, bountyInfiniteQuery, bountyQueryKey, nextBountyCursor,
  createBountyFilterOperations, createGoScreener, clampBountyQuery, REWARD_MINTS,
  BOUNTY_PUBLIC_PHASES, timeLeftMatches } from '../reconstruction/go-screener-data/screener.mjs';
import { APP_ROOT, DIRECTORY, PROOF, buildGoScreenerProof, verifyGoScreener } from '../reconstruction/go-screener-data/verify.mjs';
import { sha256 } from '../scripts/original-contracts/source.mjs';

const NOW = Date.parse('2026-01-01T00:00:00Z');
const date = (delta) => new Date(NOW + delta).toISOString();
const filters = (changes = {}) => ({ q:'', statuses:[], rewardTokens:[], timeLeft:null, rewardUsdMin:null, rewardUsdMax:null, ...changes });
const task = (taskId, fields = {}) => ({ taskId, title:`title-${taskId}`, bodyMarkdown:'body', status:'PENDING_RESOLUTION',
  expiresAt:date(3600000), rewardLegs:[], createdAt:date(-1000), ...fields });
const parsedResult = (items, fields={}) => ({ items, ...fields });
function transport(pages, parse = (value) => value) {
  const calls=[], events=[];
  return { calls, events, client:{ get(route, options) {
    calls.push({route,options});events.push('get');
    return { async json() {events.push('json');const page=pages.shift();if(page instanceof Error)throw page;return page;} };
  } }, responseSchema:{ parse(value) {events.push('parse');return parse(value);} } };
}
const enriched = (tasks) => ({ bounties:tasks.map((t)=>({...t,id:t.taskId})),liveTokens:new Map() });

test('complete filter builder preserves sort/phase precedence, time intersections, mint and raw reward bounds',()=>{
  let samples=0;
  const query=buildBountyFilters({ sortKey:'time-asc', filters:filters({q:'  text  ',statuses:['CLOSED'],rewardTokens:['SOL'],
    rewardUsdMin:1,rewardUsdMax:9000,timeLeft:'lt-3d'}),now:()=>{samples++;return NOW;} });
  assert.deepEqual(query,{sort:'expiresAt',order:'asc',q:'text',phase:'OPEN',rewardMints:[REWARD_MINTS.SOL],
    rewardTotalUsdGte:1,rewardTotalUsdLte:9000,expiresAtGte:date(0),expiresAtLte:date(86400000)});
  assert.equal(samples,1);
  const near=buildBountyFilters({sortKey:'time-asc',filters:filters(),nearMe:{lat:0,lng:0,radiusKm:25},now:()=>NOW});
  assert.equal(near.sort,'distance');assert.equal(near.order,'asc');assert.equal(near.phase,'OPEN');
  assert.equal(buildBountyFilters({sortKey:'unknown',filters:filters(),now:()=>NOW}).phase,BOUNTY_PUBLIC_PHASES);
  assert.deepEqual(buildBountyFilters({sortKey:'recent',filters:filters({statuses:['OPEN','CLOSED'],rewardUsdMin:0,rewardUsdMax:10000}),now:()=>NOW}),
    {sort:'createdAt',order:'desc',phase:'OPEN,CLOSED'});
});

test('query clamp is original UTF16 slicing, with nullish identity and no new Unicode/schema policy',()=>{
  assert.equal(clampBountyQuery(undefined),undefined);assert.equal(clampBountyQuery(null),null);
  const value='a'.repeat(255)+'😀';const result=clampBountyQuery(value);
  assert.equal(result.length,256);assert.equal(result.charCodeAt(255),0xd83d);
});

test('lazy query JSON→schema order retains every field and explicit geo/feature/first-page gates',async()=>{
  const result=parsedResult([],{nextCursor:'opaque'}),io=transport([result,result]);
  const query=bountyInfiniteQuery({q:'q',creatorAddress:'creator',coinAddress:'mint',rewardMints:['a','b'],status:'PENDING_RESOLUTION',phase:'OPEN',
    expiresAtGte:'gte',expiresAtLte:'lte',rewardTotalUsdGte:0,rewardTotalUsdLte:12,likeCountGte:0,submissionCountGte:3,
    creatorXFollowerCountGte:7,includeBanned:true,sort:'creatorXFollowerCount',order:'desc',lat:0,lng:-1,radiusKm:0,facets:true},
    {...io,xFeatures:true});
  assert.equal(io.calls.length,0);assert.equal(query.enabled,true);assert.equal(query.initialPageParam,undefined);
  assert.strictEqual(await query.queryFn({pageParam:undefined}),result);
  assert.deepEqual(io.events,['get','json','parse']);
  assert.deepEqual(io.calls[0],{route:'bounties/v2/tasks',options:{searchParams:{q:'q',creatorAddress:'creator',coinAddress:'mint',rewardMints:'a,b',
    status:'PENDING_RESOLUTION',phase:'OPEN',expiresAtGte:'gte',expiresAtLte:'lte',rewardTotalUsdGte:'0',rewardTotalUsdLte:'12',likeCountGte:'0',
    submissionCountGte:'3',creatorXFollowerCountGte:'7',includeBanned:'true',sort:'creatorXFollowerCount',order:'desc',lat:'0',lng:'-1',radiusKm:'0',limit:'24',facets:'true'}}});
  await query.queryFn({pageParam:'opaque'});
  assert.equal(io.calls[1].options.searchParams.cursor,'opaque');assert.ok(!Object.hasOwn(io.calls[1].options.searchParams,'facets'));
});

test('feature-off, incomplete/nonfinite geo, undefined-only limit and raw enabled behavior remain visible',async()=>{
  const io=transport([parsedResult([]),parsedResult([])]);
  const query=bountyInfiniteQuery({sort:'creatorXFollowerCount',creatorXFollowerCountGte:9,limit:null,enabled:null,
    lat:0,lng:1,radiusKm:Infinity},{...io,xFeatures:false});
  assert.equal(query.enabled,null);
  await query.queryFn({pageParam:0});
  assert.deepEqual(io.calls[0].options.searchParams,{limit:'null',cursor:0});
  assert.equal(query.queryKey[8],null);assert.equal(query.queryKey[17],null);
  assert.deepEqual(query.queryKey.slice(-3),[null,null,null]);
  const valid=bountyInfiniteQuery({limit:0,lat:0,lng:0,radiusKm:-1},{...io,xFeatures:false});
  await valid.queryFn({pageParam:undefined});assert.equal(io.calls[1].options.searchParams.limit,'0');
  assert.deepEqual(valid.queryKey.slice(-3),[0,0,-1]);
});

test('cursor nullish fallback retains empty string while request facets/cursor predicates differ',async()=>{
  assert.equal(nextBountyCursor({}),undefined);assert.equal(nextBountyCursor({nextCursor:null}),undefined);
  assert.equal(nextBountyCursor({nextCursor:''}),'');
  const io=transport([parsedResult([])]),query=bountyInfiniteQuery({facets:true},{...io,xFeatures:false});
  await query.queryFn({pageParam:''});assert.deepEqual(io.calls[0].options.searchParams,{limit:'24'});
  assert.equal(bountyQueryKey({facets:'yes'})[19],null);assert.equal(bountyQueryKey({facets:true})[19],true);
});

test('query capability errors and parser transformations are retained without retries or fallback records',async()=>{
  const failure=Object.assign(new Error('abort'),{name:'AbortError'}),io=transport([failure]);
  const query=bountyInfiniteQuery(undefined,{...io,xFeatures:false});await assert.rejects(query.queryFn({}),e=>e===failure);
  assert.deepEqual(io.events,['get','json']);
  const raw={raw:true},parsed=parsedResult([]),changed=transport([raw],v=>{assert.strictEqual(v,raw);return parsed;});
  assert.strictEqual(await bountyInfiniteQuery({}, {...changed,xFeatures:false}).queryFn({}),parsed);
  const bad=transport([raw],()=>{throw failure;});await assert.rejects(bountyInfiniteQuery({}, {...bad,xFeatures:false}).queryFn({}),e=>e===failure);
  assert.equal(bad.calls.length,1);
});

test('phase and local time predicates retain separate clocks, invalid/missing dates and strict seven-day boundary',()=>{
  let reads=0;const ops=createBountyFilterOperations({now:()=>{reads++;return NOW;}});
  assert.equal(ops.classifyPhase('DRAFT',date(1)),'DRAFT');assert.equal(reads,0);
  assert.equal(ops.classifyPhase('PENDING_RESOLUTION','bad'),'OPEN');assert.equal(reads,0);
  assert.equal(ops.classifyPhase('PENDING_RESOLUTION',date(0)),'PENDING_RESOLUTION');assert.equal(reads,1);
  assert.equal(ops.classifyPhase('PENDING_RESOLUTION',undefined),'OPEN');assert.equal(reads,1);
  assert.equal(timeLeftMatches(task('a',{expiresAt:date(604800000)}),'gte-7d',NOW),false);
  assert.equal(timeLeftMatches(task('a',{expiresAt:date(604800001)}),'gte-7d',NOW),true);
  const counts=ops.countTimeLeft([task('a',{expiresAt:undefined}),task('b',{expiresAt:'bad'})]);
  assert.deepEqual([...counts],[['lt-24h',2],['lt-3d',2],['lt-7d',2],['gte-7d',2]]);
});

test('local facet filtering preserves raw missing-USD and token/phase/text rules without sorting',()=>{
  const ops=createBountyFilterOperations({now:()=>NOW}),a=task('a',{title:'Hello',bodyMarkdown:'WORLD',rewardTotalUsd:undefined,coinAddress:REWARD_MINTS.SOL}),
    b=task('b',{title:'hello',status:'DRAFT',rewardLegs:[{mintAddress:REWARD_MINTS.SOL}]}),c=task('c',{status:'CLOSED',rewardTotalUsd:0});
  assert.deepEqual(ops.filterTasks([a,b,c],filters({q:'world',statuses:['OPEN'],rewardTokens:['SOL'],rewardUsdMin:100})),[a]);
  const facets=ops.facets([task('x',{rewardLegs:[{mintAddress:'m'},{mintAddress:'m'}]}),task('y',{status:'CLOSED',rewardLegs:[{mintAddress:'n'}]})]);
  assert.deepEqual(facets.rewardMints,[{key:'m',count:2},{key:'n',count:1}]);
  assert.deepEqual(facets.phase,[{key:'OPEN',count:1},{key:'CLOSED',count:1}]);
});

test('complete plan→two parsed query results→facets/enrichment/feed handoff keeps display order and proxy overrides',async()=>{
  const a=task('a',{title:'does not match local q',status:'CLOSED',rewardLegs:[{mintAddress:'reward'},{mintAddress:'reward'}],coinAddress:'coin'}),
    b=task('b',{title:'still served',rewardLegs:[{mintAddress:'coin'}],coinAddress:'last'});
  const io=transport([parsedResult([a],{nextCursor:'next'}),parsedResult([b]),parsedResult([],{facets:{phase:[]}})]),seen=[];
  const liveTokens=new Map([['reward',{mint:'reward',label:'explicit snapshot'}]]);
  const model=createGoScreener({...io,xFeatures:false,now:()=>NOW,enrichTasks:(tasks)=>{seen.push(tasks);return {bounties:tasks.map(t=>({...t,id:t.taskId,token:{mint:'reward'}})),liveTokens};}});
  const props={filters:filters({q:'matching',statuses:['OPEN']}),sortKey:'reward-desc',viewMode:'grid'};
  const plan=model.plan(props),first=await plan.listing.queryFn({}),next=plan.listing.getNextPageParam(first),second=await plan.listing.queryFn({pageParam:next}),proxy=await plan.phaseFacets.queryFn({});
  assert.deepEqual(io.calls.map(c=>c.options.searchParams.limit),['24','24','1']);
  assert.equal(io.calls[0].options.searchParams.phase,'OPEN');assert.equal(io.calls[2].options.searchParams.phase,BOUNTY_PUBLIC_PHASES);
  const load=()=>{},ref={marker:true};
  const view=model.derive({...props,listingResult:{data:{pages:[first,second]},isError:true,isLoading:true,hasNextPage:true,isFetchingNextPage:false,fetchNextPage:load},facetsResult:{data:{pages:[proxy]}},sentinelRef:ref});
  assert.deepEqual(view.tasks,[a,b]);assert.strictEqual(seen[0],view.tasks);assert.deepEqual(view.items.map(i=>i.bounty.id),['a','b']);
  assert.strictEqual(view.items[0].resolvedToken,liveTokens.get('reward'));assert.equal(view.items[0].key,'screener-bounty-a');
  assert.deepEqual(view.facets.phase,[]);assert.equal(view.body,'feed');assert.deepEqual(view.visibleMints,['reward','coin','last']);
  assert.deepEqual(view.sentinel,{hasMore:true,isLoading:false,onLoadMore:load});assert.strictEqual(view.footerProps.sentinelRef,ref);assert.equal(view.footerProps.visibleCount,2);
  assert.deepEqual(view.feedProps,{disableHoverCards:true,feedKind:'bounties',items:view.items,viewMode:'grid'});
});

test('duplicate ids use last enriched entry per raw occurrence; missing enrichment does not rewrite raw-count body',()=>{
  const a=task('a'),missing=task('missing'),chosen={id:'a',createdAt:'invalid',title:'last'};
  const model=createGoScreener({now:()=>NOW,enrichTasks:()=>({bounties:[{id:'a',createdAt:date(0)},chosen],liveTokens:new Map()})});
  const props={filters:filters(),listingResult:{data:{pages:[{items:[a,a,missing]}]}},facetsResult:{}};
  const view=model.derive(props);assert.equal(view.tasks.length,3);assert.equal(view.items.length,2);
  assert.strictEqual(view.items[0].bounty,chosen);assert.strictEqual(view.items[1].bounty,chosen);assert.ok(Number.isNaN(view.items[0].timestamp));
  assert.equal(view.body,'feed');assert.equal(view.footerProps.visibleCount,3);
  const again=model.derive(props);assert.strictEqual(again.facets.status,view.facets.status);
});

test('empty loading/error/near-me precedence and lazy planning introduce no observer/provider work',()=>{
  let enrichments=0;const io=transport([]),model=createGoScreener({...io,xFeatures:false,now:()=>NOW,enrichTasks:(tasks)=>{enrichments++;return enriched(tasks);}});
  model.plan({filters:filters(),sortKey:'recent'});assert.equal(io.calls.length,0);
  for(const [state,expected]of[[{isLoading:true,isError:true},'loading'],[{isError:true},'error'],[{},'empty']]) {
    const view=model.derive({filters:filters(),nearMe:{lat:0,lng:0,radiusKm:25},listingResult:state,facetsResult:{}});
    assert.equal(view.body,expected);assert.equal(view.nearMeActive,true);assert.equal(view.subscribeVisible,false);
  }
  assert.equal(enrichments,3);assert.equal(io.calls.length,0);
});

const proof=await buildGoScreenerProof();
async function isolated(t) {
  const root=await mkdtemp(path.join(os.tmpdir(),'go screener public source '));t.after(()=>rm(root,{recursive:true,force:true}));
  const files=new Set(['evidence/web/manifest.json','recovered/modules.json',PROOF,`${DIRECTORY}/screener.mjs`,proof.origin.capture.source,
    ...proof.factories.map(f=>f.source),...Object.keys(proof.dependencies)]);
  for(const file of files){await mkdir(path.dirname(path.join(root,file)),{recursive:true});await copyFile(path.join(APP_ROOT,file),path.join(root,file));}
  return root;
}
test('origin/import/lazy context and complete source proof replay only public inputs at a path with spaces',async(t)=>{
  const checked=await verifyGoScreener(await isolated(t));assert.equal(checked.origin.capture.url,'https://pump.fun/go');
  assert.equal(checked.origin.actualElement.tag,'$L11a');assert.equal(checked.limits.directBountiesRouteCapture,false);
});
test('resealed query predicate corruption and physically missing parser variants fail original source checks',async(t)=>{
  const root=await isolated(t),file=path.join(root,DIRECTORY,'screener.mjs'),original=await readFile(file,'utf8');
  await writeFile(file,original.replace('D && null == t','D && null != t'));await assert.rejects(buildGoScreenerProof(root),/complete lazy GET/);
  await writeFile(file,original);const indexFile=path.join(root,'recovered/modules.json'),index=JSON.parse(await readFile(indexFile,'utf8'));
  index.modules=index.modules.filter(m=>!m.sha256.startsWith('390e9ed491c2'));await writeFile(indexFile,JSON.stringify(index));
  await assert.rejects(buildGoScreenerProof(root),/physical variant census 711902/);
});
test('a rehashed altered Flight import cannot substitute static ID mentions for an actual main-app component',async(t)=>{
  const root=await isolated(t),file=path.join(root,proof.origin.capture.source),raw=await readFile(file,'utf8');
  assert.ok(raw.includes('11a:I[768385'));
  const changed=Buffer.from(raw.replace('11a:I[768385','11a:I[768386'));await writeFile(file,changed);
  const manifestFile=path.join(root,'evidence/web/manifest.json'),manifest=JSON.parse(await readFile(manifestFile,'utf8'));
  const entry=manifest.records.find(r=>r.path===proof.origin.capture.source);entry.sha256=sha256(changed);entry.bytes=changed.length;await writeFile(manifestFile,JSON.stringify(manifest));
  await assert.rejects(buildGoScreenerProof(root),/768385|strictly equal/);
});
