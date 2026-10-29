// Explicit synthetic snapshots and render/query ports; never an app/provider.
import * as React from 'react';
import * as jsx from 'react/jsx-runtime';
import {c} from 'react/compiler-runtime';
import {createRoot} from 'react-dom/client';
import {createLiveReadState} from './client.mjs';
const el=React.createElement,events=[],listeners=new Set(),active=new Set();
const first={id:'most-row'},second={id:'cap-row'},clip={id:'clip-row'};
const next=(sort)=>()=>{events.push({type:'next-page',sort});return Promise.resolve('synthetic unawaited promise');};
const mostNext=next('most_viewers'),capNext=next('market_cap');
let state={nsfw:false,prefix:'prefix-one',blocked:false,hero:{data:[],isLoading:true},
  most:{data:undefined,isLoading:true,hasNextPage:true,isFetchingNextPage:false,fetchNextPage:mostNext},
  cap:{data:undefined,isLoading:true,hasNextPage:true,isFetchingNextPage:false,fetchNextPage:capNext},
  clips:{data:[],isLoading:true,hasNextPage:false,isFetchingNextPage:false,fetchNextPage:next('clips')},
  recordings:{data:[],isLoading:true,hasNextPage:false,isFetchingNextPage:false,fetchNextPage:next('recordings')}};
const subscribe=(fn)=>{listeners.add(fn);return()=>listeners.delete(fn);};
const useScope=()=>React.useSyncExternalStore(subscribe,()=>state);
let serial=0,latest,previousResult,previousHeroKey,previousHeroFn,previousSectionOptions;
const lastOptions=new Map(),lastRows=new Map();
class TrackedIntersectionObserver{
  constructor(callback,options){this.id=++serial;this.inner=new IntersectionObserver((entries)=>{
    events.push({type:'intersection',id:this.id,intersecting:entries.map(e=>e.isIntersecting)});callback(entries,this);
  },options);events.push({type:'observer-create',id:this.id,options});}
  observe(node){active.add(this.id);events.push({type:'observe',id:this.id});this.inner.observe(node);}
  disconnect(){active.delete(this.id);events.push({type:'disconnect',id:this.id});this.inner.disconnect();}
  unobserve(node){this.inner.unobserve(node);}
  takeRecords(){return this.inner.takeRecords();}
}
const Skeleton=React.forwardRef(({className},ref)=>el('div',{ref,'data-testid':'synthetic-skeleton',
  'data-admission':className==='opacity-0'?'true':'false',style:{height:className==='opacity-0'?'300px':'800px'}},'Synthetic skeleton'));
const empty=()=>null, router={push:(path)=>events.push({type:'router-port',path})};
const listing={fetchCoins:async(options)=>{events.push({type:'coins-port',options});return[];},
  fetchSection:async(options)=>{events.push({type:'section-port',options});return[];},
  nextLivePage:function syntheticExactPagerInterface(){},selectLivePages:function syntheticExactSelectorInterface(){},livePageIdentity:e=>e,
  LIVE_SORTS:{FEATURED:'featured',MARKET_CAP:'market_cap',MOST_VIEWERS:'most_viewers'},LIVE_CARD_COUNTS:{extraSmall:2,small:3,large:4}};
const modules={
  761459:{useInfiniteQuery:(options)=>{const s=useScope();lastOptions.set(options.queryKey[1],options);events.push({type:'section-query',sort:options.queryKey[1]});return options.queryKey[1]==='most_viewers'?s.most:s.cap;}},
  690877:{useQuery:(options)=>{lastOptions.set('hero',options);return useScope().hero;}},
  369091:{useIpfsPrefix:()=>({ipfsPrefix:useScope().prefix})},358893:{M:()=>useScope().nsfw},
  369731:{HeroCarousel:({livestreams})=>el('div',{'data-testid':'synthetic-hero'},String(livestreams.length))},
  187807:{HeroStage:({children})=>el('div',{style:{height:'60px'}},children)},218921:{PaginationDotsSkeleton:empty},
  918391:{f:()=>el('span',{},'Synthetic hero loading')},829010:{F:'synthetic'},
  157633:{kK:empty,S:empty},426091:{c:(...x)=>x.filter(Boolean).join(' ')},
  458310:{default:({href,children})=>el('a',{href:'#navigation-withheld','data-original-href':href,onClick:e=>e.preventDefault()},children)},
  398902:{f:()=>({t:s=>s})},647145:{X:(props)=>{const id=props.livestreams[0]?.id??'empty';lastRows.set(id,props);
    return el('section',{'data-testid':'synthetic-rows','data-row':id,'data-eager':String(props.eager),style:{height:'800px'}},
      id,el('button',{type:'button',onClick:props.onScrollNearEnd},'Synthetic near end'));}},
  314982:{SectionSkeleton:Skeleton},599077:{useRouter:()=>router},79472:{V:()=>useScope().blocked},
  327294:{LivestreamBlockedMessage:()=>el('p',{'data-testid':'synthetic-blocked'},'Synthetic blocked')},
};
const flow=createLiveReadState({React,jsx,compiler:{c},modules,listing,projectHeroCoin:e=>e,
  useClipsSection:(options)=>{events.push({type:'clips-port',sectionId:options.sectionId});const s=useScope();return options.sectionId==='trending-clips'?s.clips:s.recordings;},
  FloatingControl:empty,dom:{IntersectionObserver:TrackedIntersectionObserver}});
const seed=[],initialSections=[seed,seed,seed,seed,seed,seed];
let commits=0;
function Probe(){const section=flow.useSection({livePageSort:'most_viewers',initialData:seed});
  flow.useHero({initialData:seed});React.useEffect(()=>{const hero=lastOptions.get('hero'),options=lastOptions.get('most_viewers');
    latest={sameSectionResult:previousResult===section,sameHeroKey:previousHeroKey===hero.queryKey,sameHeroFn:previousHeroFn===hero.queryFn,
      sameSectionOptions:previousSectionOptions===options,heroKey:[...hero.queryKey],sectionKey:[...options.queryKey],sectionData:section.data.map(x=>x.id),
      sectionKeys:Object.keys(section)};previousResult=section;previousHeroKey=hero.queryKey;previousHeroFn=hero.queryFn;previousSectionOptions=options;commits++;});return null;}
function Host(){useScope();return el(React.Fragment,{},el(flow.LiveHomepage,{initialHeroData:seed,initialSectionData:initialSections}),el(Probe));}
const root=createRoot(document.getElementById('root'));root.render(el(Host));
const change=(patch)=>{state={...state,...patch};for(const fn of listeners)fn();};
window.harness={observe:()=>({commits,latest,activeObservers:active.size,subscriptions:listeners.size,events:[...events],rowIds:[...document.querySelectorAll('[data-testid="synthetic-rows"]')].map(e=>e.dataset.row)}),
  settleMostEmpty:()=>change({most:{...state.most,isLoading:false,data:{pages:[[]]}}}),
  settleTwo:()=>change({most:{...state.most,isLoading:false,data:{pages:[[first]]}},cap:{...state.cap,isLoading:false,data:{pages:[[second]]}}}),
  settleClips:()=>change({clips:{...state.clips,isLoading:false,data:[clip]}}),
  changePrefix:()=>change({prefix:'prefix-two'}),errorOnly:()=>change({most:{...state.most,isError:true,error:Error('synthetic port error')}}),
  nearEnd:()=>{const props=lastRows.get('most-row');if(!props)throw Error('missing source row handoff');return props.onScrollNearEnd();},
  setFetching:()=>change({most:{...state.most,isFetchingNextPage:true}}),
  scrollAdmission:()=>{const node=document.querySelector('[data-admission="true"]');if(!node)throw Error('no pending source admission target');window.scrollTo({top:window.scrollY+node.getBoundingClientRect().top-300,behavior:'instant'});},
  blocked:()=>change({blocked:true}),unmount:()=>root.unmount(),
};
