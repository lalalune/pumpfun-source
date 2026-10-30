import {jsx,jsxs,Fragment}from'../../packages/frontend/node_modules/react/jsx-runtime.js';import{memo,createContext,useContext}from'../../packages/frontend/node_modules/react/index.js';import{c as useMemoCache}from'../../packages/frontend/node_modules/react/compiler-runtime.js';import{createCoinPositionWorkflow}from'../../reconstruction/coin-position-display/client.mjs';
export const IMAGE='data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="40"%3E%3Crect width="40" height="40" fill="purple"/%3E%3C/svg%3E';
export const NORMAL={positionUsd:12.5,isClosed:false,exitProceedsUsd:null,netPnlUsd:-3};
export const ROW={tag:'opaque raw row',servedProjection:NORMAL};
export const PROVIDER={isLoading:true,rows:{},price:null,clientReady:true,language:'en'};
export const BASE={mint:'MiNt',authorAddress:'synthetic-user',symbol:'$SYN',name:'Synthetic coin',imageUri:IMAGE,chainId:'ton:-239',pollIntervalMs:5200};
export function createPositionHost(){
 const Context=createContext(PROVIDER),records={read:[],lookups:[],price:[],live:[],served:[],avatar:[],localImage:[],chain:[],time:[],badge:[],skeleton:[],formats:[],actions:0};
 const t=(key)=>key;
 function Skeleton(p){records.skeleton.push(p);return jsx('span',{'data-port':'skeleton',children:'supplied skeleton'});}
 function LocalImage(p){records.localImage.push(p);return jsx('img',{src:p.src,alt:p.alt,width:p.width,height:p.height,'data-port':'local-image'});}
 function CoinAvatar(p){records.avatar.push(p);return jsxs('span',{'data-port':'coin-avatar',children:[jsx('img',{src:p.coin.image_uri??IMAGE,alt:'Synthetic image',width:p.size,height:p.size}),p.children]});}
 function ChainBadge(p){records.chain.push(p);return jsx('span',{'data-port':'chain',children:'supplied chain'});}
 function RelativeTime(p){records.time.push(p);return jsx('time',{'data-port':'relative',children:String(p.timestamp)});}
 function ClosedBadge(p){records.badge.push(p);return jsx('span',{'data-testid':p['data-testid'],children:p.children});}
 const money=(kind,value)=>{records.formats.push({kind,value});return kind+':'+String(value);};
 const workflow=createCoinPositionWorkflow({jsx,jsxs,Fragment,useMemoCache,memo,Skeleton,classNames:(...xs)=>xs.filter(Boolean).join(' '),
  usePositions(input){const p=useContext(Context);records.read.push(input);return{isLoading:p.isLoading,positionFor(key){records.lookups.push(key);return p.rows[key];}};},
  useLivePrice(mint){const p=useContext(Context);records.price.push(mint);return p.price;},projectLivePosition(row,price){records.live.push({row,price});return row?.liveProjection??null;},projectServedPosition(row){records.served.push(row);return row?.servedProjection??null;},
  LocalImage,useTranslation(){const p=useContext(Context);return{t,i18n:{language:p.language}};},ChainBadge,CoinAvatar,pnlTone:()=> 'supplied-tone',moneyCompact:value=>money('compact',value),moneyValue:value=>money('value',value),moneySigned:value=>money('signed',value),RelativeTime,ClosedBadge,
  useClientReady:()=>useContext(Context).clientReady,formatLargeAmount:({value})=>money('large',value),makeNumberFormatter:(locale,options)=>new Intl.NumberFormat(locale,options),formatFullDate:(value,locale)=>'full:'+locale+':'+value,formatDate:({timestampMs})=>'date:'+timestampMs,normalizeNumberText:value=>value,localeFor:language=>language==='en'?'en-US':null,defaultLocale:'en-US',parseTimestamp:value=>typeof value==='number'&&Number.isFinite(value)?value:null});
 return{...workflow,Context,records};
}
