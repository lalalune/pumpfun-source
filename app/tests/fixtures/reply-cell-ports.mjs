import React from '../../packages/frontend/node_modules/react/index.js';
import {jsx,jsxs} from '../../packages/frontend/node_modules/react/jsx-runtime.js';
import {c as useMemoCache} from '../../packages/frontend/node_modules/react/compiler-runtime.js';
import {createReplyCell,createMainReplyRenderers} from '../../reconstruction/reply-cell/client.mjs';
export const DATA_IMAGE='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="teal"/></svg>');
export const REPLY={replyId:'synthetic-reply',userId:'synthetic-user',authorCcUserId:'synthetic-author',content:'Authored reply @text\nsecond line',createdAt:'2026-10-30T00:00:00.000Z',likeCount:2,likedByViewer:false,caller:{username:'  Display name  ',walletAddress:'11111111111111111111111111111111',avatarUrl:DATA_IMAGE}};
export function createReplyHost({base58,...options}){
 const records={order:[],buttons:[],avatars:[],profileLinks:[],hovers:[],social:[],times:[],text:[],media:[],mute:[],share:[],like:[],verified:[],own:[],URI:[],profileClicks:0,toggles:0};
 const t=(key,args)=>key+(args?' '+JSON.stringify(args):'');
 const record=(name,props)=>{records[name].push(props);return props;};
 const sourceUri=options.sourceUri??{D(value,prefix){records.URI.push({method:'D',value,prefix});if(!value.startsWith('data:'))throw new Error('Authored URI port admits data images only');return value;},d(value){records.URI.push({method:'d',value});if(!value.startsWith('data:'))throw new Error('Authored URI port admits data images only');return false;}};
 function Avatar(props){record('avatars',props);return jsx('img',{src:props.src??DATA_IMAGE,alt:props.alt,width:props.width,height:props.height,className:props.className,'data-port':'avatar','data-address':props.address});}
 function ProfileLink({profileId,children,onClick,...props}){record('profileLinks',{profileId,...props});return jsx('a',{...props,'data-profile-id':profileId,onClick(e){e.preventDefault();records.profileClicks++;onClick?.(e);},children});}
 function ProfileHover(props){record('hovers',props);return jsx('span',{'data-port':'profile-hover','data-user-address':props.userAddress,children:props.children});}
 function SocialLink(props){record('social',props);return jsx('span',{'data-port':'social',children:'Social port'});}
 function RelativeTime(props){record('times',props);return jsx('time',{dateTime:props.timestamp,'data-port':'relative-time',children:'Time port'});}
 function RichText(props){record('text',props);return jsx('span',{'data-port':'174251.f',children:props.content});}
 function ImagePreview(props){record('media',props);return jsx('img',{src:props.src,alt:'Authored media port','data-testid':props.testId,className:props.className});}
 function MuteMenu(props){record('mute',props);return jsx('span',{'data-port':'mute-menu',children:'Inert menu port'});}
 function ShareMenu(props){record('share',props);return jsx('span',{'data-port':'share-menu','data-share-path':props.sharePath,children:props.children});}
 const icon=name=>props=>jsx('span',{'data-icon':name,className:props.className,'aria-hidden':true,children:name});
 const node=(type,props,key)=>{if(type==='button')records.buttons.push(props);return jsx(type,props,key);};
 const many=(type,props,key)=>{if(type==='button')records.buttons.push(props);return jsxs(type,props,key);};
 const ReplyCell=createReplyCell({jsx:node,jsxs:many,useMemoCache,classNames:(...x)=>x.filter(Boolean).join(' '),base58,sourceUri,
 Avatar,ProfileHover,ProfileLink,SocialLink,RelativeTime,RichText,ImagePreview,MuteMenu,ShareMenu,VerifiedBadge:()=>jsx('i',{'data-port':'verified',children:'Badge port'}),
 HeartFilled:icon('liked'),HeartOutline:icon('unliked'),ShareIcon:icon('share'),CommentIcon:icon('comment'),
 useTranslation(){records.order.push('translation');return{t};},useIpfsPrefix(){records.order.push('IPFS');return{ipfsPrefix:'https://synthetic.invalid/ipfs/'};},
 useVerified(id){records.order.push('verified');records.verified.push(id);return options.verified??false;},
 useOwnId(){records.order.push('own-hook');return id=>{records.order.push('own-predicate');records.own.push(id);return options.own?.has(id)??false;};},
 useReplyLike(input){records.order.push('like-hook');records.like.push(input);return{isLiked:options.isLiked??input.likedByViewer,likeCount:options.likeCount??input.likeCount,toggle(){records.order.push('like-toggle');records.toggles++;options.onToggle?.();}};},
 });
 return{ReplyCell,renderers:createMainReplyRenderers({jsx,ReplyCell}),records,options};
}
