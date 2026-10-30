import React,{useSyncExternalStore}from'react';
import{createRoot}from'react-dom/client';
import{c}from'react/compiler-runtime';
import*as jsxRuntime from'react/jsx-runtime';
import{createMobileFeedList}from'../client.mjs';
const jsx=React.createElement,listeners=new Set(),scrollListeners=new Set(),calls=[],latest={};
const callout=(key,mint=key,mediaUrl='opaque media')=>({type:'callout',key,entry:{key,userId:'supplied-user-'+key,coinMint:mint,mediaUrl}});
const rows=[callout('one','alias'),{type:'trade',key:'trade'},{type:'reply',key:'reply',row:{callout:{coinMint:'reply-actual',author:{walletAddress:'supplied-reply-author'}}},coin:{mint:'reply-mint',symbol:'FALLBACK',chainId:7},xUsername:'supplied-x'},{type:'quote',key:'quote',row:{},coin:{mint:'quote-mint',symbol:'QUOTE',chainId:8}},{type:'repost',key:'repost',reposter:{address:'supplied-reposter',name:' Reposter '},callout:{coinMint:'repost-mint',calloutId:'supplied-callout',author:{walletAddress:'supplied-author',username:' Author ',avatarUrl:'supplied-avatar'},createdAtMs:123,note:'supplied note'},coin:{mint:'repost-mint',symbol:'$REPOST',chainId:9}},callout('two','pack-missing'),callout('three','collectible'),callout('perp','filtered-mint')];
const showNewCallouts=o=>calls.push(['show',o]),fetchNextPage=()=>calls.push(['fetch-next']);
const blankFeed=()=>({rows:[],isLoadingHistory:true,error:null,pendingNewCount:0,pendingPreview:[],showNewCallouts,hasNextPage:false,hasUnseen:false,isFetchingNextPage:false,fetchNextPage});
let scrollY=9,state={feed:blankFeed(),tab:'for-you',signedOut:false,coins:[],loading:false,users:undefined,cards:new Map(),perps:false,packs:false,hidden:[]};
const subscribe=fn=>{listeners.add(fn);return()=>listeners.delete(fn);},snapshot=()=>state;
const usePorts=()=>useSyncExternalStore(subscribe,snapshot,snapshot);
const publish=change=>{state={...state,...change};for(const fn of [...listeners])fn();};
const patchFeed=patch=>publish({feed:{...state.feed,...patch}});
const readFor=(...args)=>{calls.push(['read-for',...args]);return{provided:true,args};};
const windowPort={get scrollY(){return scrollY;},scrollTo(options){calls.push(['scroll-to',options]);},addEventListener(type,fn,options){calls.push(['listen',type,options]);scrollListeners.add(fn);},removeEventListener(type,fn){calls.push(['unlisten',type]);scrollListeners.delete(fn);}};
const PendingBanner=props=>{latest.pending={count:props.count,avatars:props.avatars};return jsx('button',{type:'button',onClick:props.onClick,'data-pending':props.count},'Supplied pending reveal');};
const LoadMore=props=>{latest.more={...props,onFetchNextPage:undefined};return jsx('button',{type:'button',onClick:props.onFetchNextPage,disabled:props.isFetchingNextPage},'Supplied pagination');};
const CalloutEntry=props=>jsx('article',{'data-callout':props.entry.key,'data-priority':String(props.mediaPriority),'data-position':props.position,'data-coin':props.coin?.name??'','data-user':props.user?.username??'','data-card':props.card?.provided??'','data-viewer':props.viewerAddress,'data-surface':props.surface},'Supplied callout '+props.entry.key);
const MainFeedRow=props=>jsx('article',{'data-main-row':props.variant,'data-symbol':props.coinSymbol,'data-chain':props.coinChainId,'data-position-read':JSON.stringify(props.positionRead??null)},'Supplied '+props.variant);
const PositionInsert=props=>jsx('span',{'data-position-insert':true,'data-mint':props.mint,'data-chain':props.chainId},'Supplied position renderer');
const RootCallout=props=>jsx('article',{'data-root-callout':true,'data-author':props.authorName,'data-href':props.href,'data-avatar':props.authorAvatarUrl},props.nameAdornment,props.children);
const Link=props=>jsx('span',{'data-profile-link':props.href},props.children);
const api=createMobileFeedList({React,compiler:c,jsxRuntime,window:windowPort,
 useFeatureFlag(key,fallback){const s=usePorts();calls.push(['flag',key,fallback]);return key==='webPerps'?s.perps:s.packs;},
 usePositionsRead(inputs){usePorts();calls.push(['positions',inputs]);return{readFor};},
 useCoins(options){const s=usePorts();calls.push(['coins',options]);return{coins:s.coins,loading:s.loading};},
 usePackCards(mints){const s=usePorts();calls.push(['packs',mints]);return{cardByMint:s.cards};},
 useUsers(options){const s=usePorts();calls.push(['users',options]);return{data:s.users};},
 isCollectibleEntry:entry=>entry.key==='three',isBase58Pubkey:mint=>['alias','pack-missing','collectible'].includes(mint),normalizeMintKey:mint=>['alias','loaded'].includes(mint)?'provided-joined-key':mint,isPerpRow:row=>row.key==='perp',
 useOpenPositionGate(options){const s=usePorts();calls.push(['gate',options]);return{shouldHide:s.hidden.includes(options.mint)};},PendingBanner,LoadMore,CalloutEntry,MainFeedRow,PositionInsert,RootCallout,Link,
 profileRoute:address=>'/provided-profile/'+address,shortenAddress:address=>'short:'+address,normalizeImage:value=>value,buildImage:options=>{calls.push(['image',options]);return'provided-image-metadata';},RepostIcon:()=>jsx('span',{'aria-hidden':true},'Repost'),EmptyIcon:()=>jsx('span',{'aria-hidden':true},'Empty'),labelText:(value,context)=>{calls.push(['label',value,context]);return'Provided error '+value;}});
const t=key=>'provided:'+key;
function Root(){const s=usePorts();return api.selectFeed({t,tab:s.tab,showFollowingSignedOut:s.signedOut,feedByTab:{'for-you':s.feed,top:s.feed,following:s.feed},address:'supplied-viewer',isLoggedIn:true,viewerFollowing:['provided-follow']});}
const root=createRoot(document.getElementById('root'));root.render(jsx(Root));
const observe=()=>({subscribers:listeners.size,scrollListeners:scrollListeners.size,scrollY,calls:structuredClone(calls),latest:structuredClone(latest),tab:state.tab});
window.harness={observe,empty(){patchFeed({rows:[],isLoadingHistory:false,error:null});},error(){patchFeed({isLoadingHistory:false,error:'supplied failure'});},provideRows(){publish({feed:{...state.feed,rows,isLoadingHistory:false,error:null,pendingNewCount:2,pendingPreview:[{key:'pending',coinMint:'alias'}],hasNextPage:true,hasUnseen:false},coins:[{mint:'alias',name:'Earlier'},{mint:'loaded',name:'Joined supplied coin',image_uri:'provided-image'},{mint:'reply-mint',symbol:'READ',chain_id:99}],users:[{address:'supplied-user-one',username:'Earlier'},{address:'supplied-user-one',username:'Joined supplied user'}],cards:new Map([['pack-missing',{provided:'provided-card'}]])});},packs(value){publish({packs:value});},coinLoading(value){publish({loading:value});},perps(value){publish({perps:value});},hideOne(value){publish({hidden:value?['alias']:[]});},tab(value){publish({tab:value,signedOut:false});},scroll(value){scrollY=value;for(const fn of [...scrollListeners])fn();},pending(value){patchFeed({pendingNewCount:value});},signedOut(value){publish({signedOut:value});},unmount(){root.unmount();return observe();}};
