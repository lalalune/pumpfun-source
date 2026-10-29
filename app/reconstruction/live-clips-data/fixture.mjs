// Authored finite host: real React/compiler, synthetic query/client/schema/metadata/price/clock ports.
import React from 'react';
import {createRoot} from 'react-dom/client';
import {c} from 'react/compiler-runtime';
import {createLiveClipsData} from './client.mjs';
let version=0,commits=0,subscribers=new Set(),result,previous,latest={},memo=[],events=[],analyticsOptions,clipOptions,coinArgs,priceArgs;
let mode='trending-clips',limit,analytics={data:undefined,isLoading:true},clips={data:undefined,isLoading:false},coins={data:[],isLoading:false},price={data:undefined,isLoading:true};
let constructorTime=1999,nowTime=1000;
const analyticsRows=[{roomName:'A',vodId:'a',viewsTotal:999},{roomName:'B',vodId:'b',viewsTotal:100}],clipRows=['A','A','A','B','C','D','A','E'].map((room,i)=>({roomName:room,clipId:String(i),viewCount:100-i,createdAt:i===0?'1970-01-01T00:00:00Z':'2026-01-01T00:00:00Z',thumbnailUrl:'synthetic-image-without-resource-consumer'}));
const metadata=['A','B','C','D','E'].map(mint=>({mint,name:'Synthetic '+mint,market_cap:7,creator:'synthetic-author',symbol:mint}));
const schemas={analytics:{synthetic:'analytics-item'},clip:{synthetic:'clip-item'}};
class Clock extends Date{constructor(){super(constructorTime);constructorTime+=1001;}static now(){events.push({type:'now',value:nowTime});return nowTime++;}}
const client={get(path,{searchParams}){events.push({type:'get',path,params:[...searchParams]});return{async json(){events.push({type:'json',method:'get'});return analyticsRows;}};},post(path,{json}){events.push({type:'post',path,json});return{async json(){events.push({type:'json',method:'post'});return clipRows;}};}};
const flow=createLiveClipsData({memoCache:n=>{memo.push(n);return c(n);},useQuery:o=>{if(o.queryKey[0]==='vod-analytics'){analyticsOptions=o;return analytics;}clipOptions=o;return clips;},useLivestreamApiClient:()=>client,
 useCoinMetadata:o=>{coinArgs=o;return coins;},useSolPrice:o=>{priceArgs=o;return price;},sectionKinds:{TRENDING_CLIPS:'trending-clips',POPULAR_RECORDINGS:'popular-recordings'},listingConstants:{LIVE_LISTING_LIMIT:24,LIVE_CARD_COUNTS:{extraSmall:2,small:3,large:4}},
 arraySchemaModule:{z:{array:schema=>({parse:value=>{events.push({type:'parse',schema:schema.synthetic});return value;}})}},analyticsItemSchema:schemas.analytics,clipItemSchema:schemas.clip,Date:Clock,
 analyticsLogger:{error:(message)=>events.push({type:'analytics-error',message})},clipLogger:{error:(message)=>events.push({type:'clip-error',message})}});
function subscribe(fn){subscribers.add(fn);return()=>subscribers.delete(fn);}const snapshot=()=>version;
function Host(){React.useSyncExternalStore(subscribe,snapshot,snapshot);memo=[];result=flow.useClipSection({sectionId:mode,limit});
 latest={sameAnalyticsOptions:previous?.analyticsOptions===analyticsOptions,sameClipOptions:previous?.clipOptions===clipOptions,sameIds:previous?.clipOptions.queryKey[1]===clipOptions.queryKey[1],sameResult:previous?.result===result,sameData:previous?.result.data===result.data,sameCoinArgs:previous?.coinArgs===coinArgs,samePriceArgs:previous?.priceArgs===priceArgs};
 previous={analyticsOptions,clipOptions,result,coinArgs,priceArgs};React.useLayoutEffect(()=>{commits++;});
 return React.createElement('main',{},React.createElement('p',{'data-testid':'status'},result.isLoading?'loading':'settled'),React.createElement('ol',{},result.data.map(row=>React.createElement('li',{key:row.id},row.id+':'+row.title))));}
const root=createRoot(document.getElementById('root'));const update=()=>{version++;for(const fn of subscribers)fn();};
window.harness={observe:()=>({commits,subscribers:subscribers.size,memo,latest,events,keys:[analyticsOptions?.queryKey,clipOptions?.queryKey],coinMints:coinArgs?.mints,ids:result?.data.map(r=>r.id),cards:result?.data,loading:result?.isLoading,resultKeys:Object.keys(result??{}),stale:[analyticsOptions?.staleTime,clipOptions?.staleTime],paging:{has:result?.hasNextPage,fetching:result?.isFetchingNextPage}}),
 async invokeAnalytics(){const one=await analyticsOptions.queryFn(),two=await analyticsOptions.queryFn();return{sameBody:one===two,count:one.length};},
 settleAnalytics(){analytics={data:analyticsRows,isLoading:false};update();},async invokeClips(){return(await clipOptions.queryFn()).length;},
 settleClips(){clips={data:clipRows,isLoading:false};coins={data:metadata,isLoading:false};update();},settlePrice(){price={data:2,isLoading:false};update();},force(){update();},
 monthly(){mode='popular-recordings';limit=2.5;update();},errorOnly(){analytics={...analytics,error:Error('synthetic query error'),isError:true};price={...price,isLoading:true};update();},
 next(){return result.fetchNextPage();},unmount(){root.unmount();}};
root.render(React.createElement(Host));
