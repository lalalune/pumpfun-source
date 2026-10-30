import React,{createContext,useContext,useMemo,useState,useSyncExternalStore}from'react';
import{createRoot}from'react-dom/client';import{c}from'react/compiler-runtime';import*as jsxRuntime from'react/jsx-runtime';
import{createProfileHoverCard}from'../client.mjs';
const jsx=React.createElement,listeners=new Set(),calls=[],timers=new Map();let timerId=0,clockTick=0,resolveWrite;
const ZERO={lastUpdatedTs:null,nativeBalance:0,nativeLamports:0,solPrice:0,tokenCount:0,totalValue:0,portfolioPnL:{totalCostBasisUsd:0,totalUnrealizedUsd:0,totalPercentage:0}};
const PROJECTION={...ZERO,lastUpdatedTs:123000,nativeBalance:1.25,tokenCount:2,totalValue:123,portfolioPnL:{totalCostBasisUsd:20,totalUnrealizedUsd:-3,totalPercentage:-15}};
const USER={username:' Supplied User ',profile_image:null,bio:'  Supplied bio.  ',followers:12,following:0};
let state={address:'fixture-address-A',userId:'fixture-user-id',disabled:false,config:{clientServerUrl:'https://supplied.invalid/client',profileApiUrl:'https://supplied.invalid/profile'},
 profile:{data:undefined,isPending:true},summary:{data:undefined,isPending:true,isError:false},pnl:{data:undefined,isPending:true,isError:false},verified:false,squads:false,clipboardMode:'defer'};
const subscribe=fn=>{listeners.add(fn);return()=>listeners.delete(fn);},snapshot=()=>state;
const publish=change=>{state={...state,...change};for(const fn of [...listeners])fn();};const usePorts=()=>useSyncExternalStore(subscribe,snapshot,snapshot);
const options={};
const HoverContext=createContext(null);
function HoverRoot(props){const[open,setOpen]=useState(false);const value=useMemo(()=>({open,toggle(){setOpen(!open);props.onOpenChange(!open);}}),[open,props.onOpenChange]);return jsx(HoverContext.Provider,{value},jsx('section',{'data-port-root':true,'data-open-delay':props.openDelay,'data-close-delay':props.closeDelay},props.children));}
function HoverTrigger(props){const ctx=useContext(HoverContext);return React.cloneElement(props.children,{'aria-expanded':ctx.open,onClick:ctx.toggle});}
function HoverContent(props){const ctx=useContext(HoverContext);return ctx.open?jsx('div',{role:'tooltip','aria-label':'Supplied profile display','data-side':props.side,'data-align':props.align,'data-collision-padding':props.collisionPadding,onClick:props.onClick},props.children):null;}
const Avatar=props=>jsx('span',{'data-avatar-address':props.address,'data-avatar-src':props.src??'', 'data-avatar-prefix':props.ipfsPrefix,'aria-label':'Supplied avatar'},'Avatar');
const VerifiedBadge=()=>jsx('span',{'aria-label':'Supplied verified badge'},'Verified');const XTooltip=props=>jsx('span',{'data-x-tooltip':true},props.children);
const {ProfileHoverCard}=createProfileHoverCard({environmentSnapshot:{default:undefined},React,compiler:c,jsxRuntime,
 useApiClientsConfig(){calls.push(['config']);return usePorts().config;},useVerifiedStatus(subject){calls.push(['verified',subject]);return usePorts().verified;},
 useProfileLookup(value){const s=usePorts();options.profile=value;calls.push(['profile',value]);return s.profile;},
 useQuery(value){const s=usePorts(),kind=value.queryKey[0]==='balanceSummary'?'summary':'pnl';options[kind]=value;calls.push(['query',kind]);return s[kind];},
 readBalanceSummary:async value=>{calls.push(['read-summary',value]);return{success:true,data:{providedProjection:PROJECTION}};},readWindowPnl:async(...args)=>{calls.push(['read-pnl',...args]);return-5;},
 normalizeBalanceSummary:value=>value?.providedProjection??ZERO,readXProfile:row=>row?.providedX??null,useFeatureFlag:()=>usePorts().squads,
 groupRoute:value=>`/supplied-squad/${value.groupId}`,shortenAddress:value=>`short:${value}`,plural:(one,many,count)=>count===1?one:many,
 formatMoney:value=>`providedMoney:${value}`,formatCompact:value=>`providedCompact:${value}`,formatSigned:value=>`providedSigned:${value}`,formatPnlClass:value=>`providedTone:${value}`,formatCount:value=>`providedCount:${value}`,formatUpdated:value=>`providedTime:${value}:${clockTick}`,
 classes:(...values)=>values.filter(Boolean).join(' '),Avatar,VerifiedBadge,XTooltip,HoverRoot,HoverTrigger,HoverContent,
 XIcon:()=>jsx('span',{'aria-hidden':true},'X'),CheckIcon:()=>jsx('span',{'aria-hidden':true},'✓'),CopyIcon:()=>jsx('span',{'aria-hidden':true},'Copy'),
 navigator:{clipboard:{writeText(value){calls.push(['clipboard',value]);return state.clipboardMode==='defer'?new Promise(resolve=>{resolveWrite=resolve;}):Promise.resolve();}}},
 setInterval(fn,delay){const id=++timerId;timers.set(id,{kind:'interval',fn,delay});calls.push(['interval',id,delay]);return id;},clearInterval(id){calls.push(['clear',id]);timers.delete(id);},setTimeout(fn,delay){const id=++timerId;timers.set(id,{kind:'timeout',fn,delay});calls.push(['timeout',id,delay]);return id;}});
const child=jsx('button',{type:'button'},'Supplied profile trigger'),follow=jsx('span',{'data-follow-slot':true},'Provided follow slot only');
function Root(){const s=usePorts();return jsx(ProfileHoverCard,{userAddress:s.address,userId:s.userId,disabled:s.disabled,children:child,fallbackUsername:'Fallback User',fallbackAvatarUrl:null,followSlot:follow,context:'Supplied context',ipfsPrefix:' https://supplied.invalid/ipfs/ ',onOpenChange:value=>calls.push(['parent-open',value])});}
const root=createRoot(document.getElementById('root'));root.render(jsx(Root));
const observe=()=>({address:state.address,subscribers:listeners.size,timers:[...timers].map(([id,t])=>({id,kind:t.kind,delay:t.delay})),calls:structuredClone(calls),
 profileOptions:options.profile,summaryOptions:options.summary?{key:options.summary.queryKey,enabled:options.summary.enabled,staleTime:options.summary.staleTime}:null,pnlOptions:options.pnl?{key:options.pnl.queryKey,enabled:options.pnl.enabled,staleTime:options.pnl.staleTime,retry:options.pnl.retry}:null});
window.harness={observe,async executeReads(){const summary=options.summary,pnl=options.pnl;const data=await summary.queryFn();const pnlValue=await pnl.queryFn();publish({profile:{data:USER,isPending:false},summary:{data,isPending:false,isError:false},pnl:{data:pnlValue,isPending:false,isError:false},verified:true});},
 social(){publish({profile:{data:{...USER,username:' ',profile_image:'https://pump.mypinata.cloud/ipfs/QmeSzchzEPqCU1jwTnsipwcBAeH7S4bmVvFGfF65iA1BY1',providedX:{x_username:' supplied ',x_profile_url:' https://supplied.invalid/x '},group_badges:[{group_id:''},{group_id:'fixture-squad',username:' ',profile_image_url:null}]},isPending:false},squads:true});},
 tickIntervals(){clockTick++;for(const t of [...timers.values()])if(t.kind==='interval')t.fn();},changeTimestamp(){publish({summary:{data:{success:true,data:{providedProjection:{...PROJECTION,lastUpdatedTs:456000}}},isPending:false,isError:false}});},
 error(){publish({summary:{data:{success:false,data:null,error:'supplied failure'},isPending:false,isError:false},pnl:{data:0,isPending:false,isError:false}});},
 pending(){publish({summary:{data:undefined,isPending:true,isError:false}});},success(){publish({summary:{data:{success:true,data:{providedProjection:PROJECTION}},isPending:false,isError:false}});},
 disabled(value){publish({disabled:value});},newAddress(){publish({address:'fixture-address-B'});},resolveClipboard(){if(!resolveWrite)throw Error('No deferred write');resolveWrite();resolveWrite=undefined;},
 unmount(){root.unmount();return observe();},cleanupEnvironment(){timers.clear();return observe();}};
