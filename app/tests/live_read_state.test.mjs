import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile,writeFile,mkdir,mkdtemp,copyFile,symlink,rm } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { createLiveReadState } from '../reconstruction/live-read-state/client.mjs';
import { APP_ROOT,DIRECTORY,recover,verify } from '../reconstruction/live-read-state/recover.mjs';
const frontend=createRequire(new URL('../packages/frontend/package.json',import.meta.url));
const React=frontend('react'),jsx=frontend('react/jsx-runtime'),compiler=frontend('react/compiler-runtime'),{renderToString}=frontend('react-dom/server');
const element=React.createElement;
function host({query={data:[],isLoading:false},infinite={data:undefined,isLoading:false},nsfw=false,prefix='synthetic-prefix',blocked=false}={}){
  const calls={coins:[],sections:[],projector:[],rows:[],skeleton:0,hero:[],links:[]};
  const listing={fetchCoins:async(options)=>{calls.coins.push(options);return[{mint:'synthetic-coin'}];},
    fetchSection:async(options)=>{calls.sections.push(options);return[{id:'synthetic-row'}];},
    nextLivePage:function syntheticPagerPort(){},selectLivePages:function syntheticSelectorPort(){},livePageIdentity:(e)=>e,
    LIVE_SORTS:{FEATURED:'featured',MARKET_CAP:'market_cap',MOST_VIEWERS:'most_viewers'},LIVE_CARD_COUNTS:{extraSmall:2,small:3,large:4}};
  const empty=()=>null;
  const modules={
    761459:{useInfiniteQuery:(options)=>{calls.infinite=options;return infinite;}},
    690877:{useQuery:(options)=>{calls.query=options;return query;}},
    369091:{useIpfsPrefix:()=>({ipfsPrefix:prefix})},358893:{M:()=>nsfw},
    369731:{HeroCarousel:({livestreams})=>{calls.hero.push(livestreams);return element('p',{},'synthetic hero');}},
    187807:{HeroStage:({children})=>element('div',{},children)},218921:{PaginationDotsSkeleton:empty},
    918391:{f:()=>element('span',{},'synthetic hero loading')},829010:{F:'synthetic-stage'},
    157633:{kK:empty,S:empty},426091:{c:(...x)=>x.filter(Boolean).join(' ')},
    458310:{default:({href,children})=>{calls.links.push(href);return element('a',{href:'#synthetic-navigation-withheld'},children);}},
    398902:{f:()=>({t:(s)=>s})},647145:{X:(props)=>{calls.rows.push(props);return element('p',{},'synthetic rows');}},
    314982:{SectionSkeleton:()=>{calls.skeleton++;return element('p',{},'synthetic skeleton');}},
    599077:{useRouter:()=>({push:()=>{throw Error('no navigation in source test');}})},
    79472:{V:()=>blocked},327294:{LivestreamBlockedMessage:()=>element('p',{},'synthetic blocked')},
  };
  const flow=createLiveReadState({React,jsx,compiler,modules,listing,
    projectHeroCoin:(coin)=>{calls.projector.push(coin);return{mint:coin.mint,title:'synthetic projected'};},
    useClipsSection:()=>{throw Error('unimplemented external clip/VOD hook must not execute in these cases');},
    FloatingControl:empty,dom:{IntersectionObserver:class{constructor(){throw Error('SSR has no observer effects');}}}});
  return{flow,calls,listing};
}
function renderHook(callback){let result;function Host(){result=callback();return null;}renderToString(element(Host));return result;}
test('complete main/live callbacks, parent context and exact credited helper pointers authenticate',async()=>{
  const p=await verify();assert.equal(p.factories.length,8);assert.equal(p.listingLinks.length,6);
  assert.deepEqual(p.origin.elementPath,['1']);assert.equal(p.external.length,5);
  assert.equal(p.limits.providerQueryRuntime,false);assert.equal(p.limits.accountActions,false);
});
test('actual hero memo/query arguments retain the NSFW-only key, direct result identity and featured reader order',async()=>{
  const query={data:[],isLoading:false,error:Error('opaque query port')};const {flow,calls}=host({query,nsfw:true,prefix:'synthetic-ipfs'});
  const seed=[];assert.strictEqual(renderHook(()=>flow.useHero({initialData:seed,staleTime:0})),query);
  assert.deepEqual(calls.query.queryKey,['live-hero-coins',true]);assert.strictEqual(calls.query.initialData,seed);assert.equal(calls.query.staleTime,0);
  assert.deepEqual(await calls.query.queryFn(),[{mint:'synthetic-coin',title:'synthetic projected'}]);
  assert.deepEqual(calls.coins,[{limit:6,offset:0,livePageSort:'featured',includeNsfw:true,ipfsPrefix:'synthetic-ipfs'}]);
  assert.deepEqual(calls.projector,[{mint:'synthetic-coin'}]);
});
test('actual section memo/query seed/key keeps nominal limit, exact pager APIs, flatten order and stripped errors',async()=>{
  const one={id:'one'},two={id:'two'},fetchNextPage=()=>{};
  const infinite={data:{pages:[[one],[two]],pageParams:[0,1]},isLoading:false,isError:true,error:Error('opaque'),fetchNextPage,hasNextPage:true,isFetchingNextPage:false};
  const {flow,calls,listing}=host({infinite,nsfw:false,prefix:'prefix-B'}),seed=[];
  const result=renderHook(()=>flow.useSection({livePageSort:'most_viewers',initialData:seed}));
  assert.deepEqual(calls.infinite.queryKey,['live-section-coins','most_viewers',false,24,'prefix-B']);
  assert.strictEqual(calls.infinite.initialData.pages[0],seed);assert.deepEqual(calls.infinite.initialData.pageParams,[0]);
  assert.strictEqual(calls.infinite.getNextPageParam,listing.nextLivePage);assert.strictEqual(calls.infinite.select,listing.selectLivePages);
  assert.deepEqual(Object.keys(result),['data','isLoading','fetchNextPage','hasNextPage','isFetchingNextPage']);
  assert.strictEqual(result.data[0],one);assert.strictEqual(result.data[1],two);assert.strictEqual(result.fetchNextPage,fetchNextPage);
  assert.deepEqual(await calls.infinite.queryFn({pageParam:77}),[{id:'synthetic-row'}]);
  assert.deepEqual(calls.sections,[{offset:77,limit:24,livePageSort:'most_viewers',includeNsfw:false,ipfsPrefix:'prefix-B'}]);
});
test('hero source renders loading/empty/data without manufacturing a query error UI',()=>{
  const loading=host({query:{data:undefined,isLoading:true,isError:true}});assert.match(renderToString(element(loading.flow.Hero,{})),/synthetic hero loading/);
  const empty=host({query:{data:[],isLoading:false,isError:true}});assert.equal(renderToString(element(empty.flow.Hero,{})),'');
  const data=[{mint:'synthetic'}],full=host({query:{data,isLoading:false}});assert.match(renderToString(element(full.flow.Hero,{})),/synthetic hero/);assert.strictEqual(full.calls.hero[0],data);
});
test('section skeleton/empty/row and near-end callbacks retain complete original handoffs',()=>{
  const h=host(),base={sectionId:'synthetic-section',titleKey:'synthetic-title',limit:3,initialData:[]};
  assert.match(renderToString(element(h.flow.Section,{...base,useFetch:()=>({data:[],isLoading:true})})),/synthetic skeleton/);
  assert.equal(renderToString(element(h.flow.Section,{...base,useFetch:()=>({data:[],isLoading:false})})), '');
  let count=0,seen;const rows=[{id:'one'}];
  const html=renderToString(element(h.flow.Section,{...base,isExpanded:true,eager:true,onShowAll:()=>{throw Error('source uses truthiness, not callback invocation');},
    useFetch:(o)=>{seen=o;return{data:rows,isLoading:false,hasNextPage:true,isFetchingNextPage:false,fetchNextPage:()=>{count++;return Promise.resolve('not awaited');}};}}));
  assert.match(html,/synthetic rows/);assert.deepEqual(seen,{limit:3,initialData:base.initialData});
  const view=h.calls.rows.at(-1);assert.strictEqual(view.livestreams,rows);assert.equal(view.scrollContainerClassName,'flex-wrap');assert.equal(view.eager,true);assert.equal(view.useViewportIntersection,true);
  assert.equal(view.onScrollNearEnd(),undefined);assert.equal(count,1);assert.ok(h.calls.links.includes('/live/synthetic-section'));
});
test('actual main-page blocked branch keeps account, query and section services external',()=>{
  const {flow,calls}=host({blocked:true});assert.match(renderToString(element(flow.LiveHomepage,{})),/synthetic blocked/);
  assert.equal(calls.query,undefined);assert.equal(calls.infinite,undefined);assert.deepEqual(calls.coins,[]);assert.deepEqual(calls.sections,[]);
});
test('the retained section registry fetch entries bind the actual existing fetchSection operation',async()=>{
  const {flow,calls}=host();assert.strictEqual(flow.sectionById.get('most-viewers'),flow.sections[0]);
  await flow.sections[0].fetch({limit:7});await flow.sections[1].fetch({livePageSort:'featured',limit:9});
  assert.deepEqual(calls.sections,[{livePageSort:'most_viewers',limit:7},{livePageSort:'featured',limit:9}]);
});
async function exportInputs(t){const result=await recover(),root=await mkdtemp(path.join(os.tmpdir(),'public main Live read inputs '));t.after(()=>rm(root,{recursive:true,force:true}));
  const files=[DIRECTORY+'/recover.mjs',DIRECTORY+'/client.mjs',DIRECTORY+'/PROVENANCE.json','scripts/original-contracts/source.mjs','scripts/settings-client-contract.mjs','evidence/web/manifest.json','recovered/modules.json',result.proof.origin.capture.source,...result.proof.factories.map(f=>f.source)];
  for(const file of new Set(files)){const p=path.join(root,file);await mkdir(path.dirname(p),{recursive:true});await copyFile(path.join(APP_ROOT,file),p);}await symlink(path.join(APP_ROOT,'node_modules'),path.join(root,'node_modules'),'dir');return root;}
test('public inputs replay without open-PR modules or private workfiles',async(t)=>{const root=await exportInputs(t);const p=await verify(root);assert.equal(p.factories.length,8);});
test('a changed intersection margin is not accepted as the complete captured controller',async(t)=>{
  const root=await exportInputs(t),file=path.join(root,DIRECTORY,'client.mjs'),text=await readFile(file,'utf8');assert.ok(text.includes('Math.floor(t / 2)'));
  await writeFile(file,text.replace('Math.floor(t / 2)','Math.floor(t / 3)'));await assert.rejects(verify(root),/complete Live read-state source differs/);
});
