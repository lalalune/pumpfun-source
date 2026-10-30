import React,{useState,useEffect}from'../../packages/frontend/node_modules/react/index.js';
import{createRoot}from'../../packages/frontend/node_modules/react-dom/client.js';
import{jsx}from'../../packages/frontend/node_modules/react/jsx-runtime.js';
import codec from'source-host-base58';
import{createReplyHost,REPLY,DATA_IMAGE}from'./reply-cell-ports.mjs';
let update,root,commits=0,rowClicks=0;
const host=createReplyHost({base58:codec.default??codec,own:new Set(),isLiked:false,likeCount:2});
const initial={mode:'linkedCallout',reply:{...REPLY,mediaUrl:DATA_IMAGE},callout:{coinMint:'synthetic-mint',calloutId:'synthetic-callout'}};
host.options.onToggle=()=>{host.options.isLiked=!host.options.isLiked;host.options.likeCount+=host.options.isLiked?1:-1;update(old=>({...old,serial:(old.serial??0)+1}));};
function App(){const[p,set]=useState(initial);update=set;useEffect(()=>{commits++;});return jsx('section',{'data-testid':'authored-ancestor',onClick:()=>{rowClicks++;},children:host.renderers[p.mode](p)});}
window.replyHarness={update(p){update(old=>({...old,...p}));},own(value){host.options.own=new Set(value?[REPLY.authorCcUserId]:[]);update(old=>({...old,serial:(old.serial??0)+1}));},unmount(){root.unmount();},state(){return{ready:!!update,commits,rowClicks,profileClicks:host.records.profileClicks,toggles:host.records.toggles,order:[...host.records.order],lastLike:host.records.like.at(-1),lastAvatar:host.records.avatars.at(-1),lastShare:host.records.share.length?{sharePath:host.records.share.at(-1).sharePath,shareTitle:host.records.share.at(-1).shareTitle}:null,lastTime:host.records.times.at(-1),lastText:host.records.text.at(-1),lastMedia:host.records.media.at(-1),links:host.records.profileLinks.slice(-2),muteCount:document.querySelectorAll('[data-port="mute-menu"]').length,rootChildren:document.getElementById('root').childElementCount};},initial};
root=createRoot(document.getElementById('root'));root.render(jsx(App,{}));
