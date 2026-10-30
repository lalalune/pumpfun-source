import {jsx,jsxs,Fragment} from '../../packages/frontend/node_modules/react/jsx-runtime.js';
import {useState,useRef,useEffect} from '../../packages/frontend/node_modules/react/index.js';
import {c as useMemoCache} from '../../packages/frontend/node_modules/react/compiler-runtime.js';
import {createCalloutCard} from '../../reconstruction/callout-card/client.mjs';

export const IMAGE='data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="36" height="36"%3E%3Crect width="36" height="36" fill="purple"/%3E%3C/svg%3E';
export const UPDATES=[0,1,2].map(i=>({id:'update-'+i,mint:'synthetic-mint',calloutId:'synthetic-callout',content:'Update '+i,createdAt:1793318400000+i,likeCount:i,likedByViewer:false,replyCount:i}));
export const BASE={authorAddress:'synthetic-address',authorUserId:'synthetic-user',authorName:'Synthetic author',authorAvatarUrl:IMAGE,authorAvatarDecoration:'supplied-decoration',createdAt:1793318400000,note:'  Supplied note  ',updates:UPDATES,testId:'source-card'};
export function createCardHost({ResizeObserver=undefined}={}){
 const records={avatar:[],hover:[],profile:[],link:[],decoration:[],keys:[],badge:[],time:[],rich:[],image:[],video:[],share:[],like:[],comments:[],prefix:[],toggle:0,author:0,root:0,linkPropsClick:0};
 const t=(key,values)=>values?key+':'+JSON.stringify(values):key;
 function Avatar(p){records.avatar.push(p);return jsx('img',{src:p.src??IMAGE,alt:p.alt,width:p.width,height:p.height,'data-port':'avatar'});}
 function ProfileHover(p){records.hover.push(p);return jsx('span',{'data-port':'hover',children:p.children});}
 function ProfileLink({children,onClick,...p}){records.profile.push({...p,onClick});return jsx('a',{href:p.href,'aria-label':p['aria-label'],'data-port':'profile',onClick(e){e.preventDefault();onClick?.(e);},children});}
 function Link({children,onClick,...p}){records.link.push({...p,onClick});return jsx('a',{href:p.href,'aria-label':p['aria-label'],'data-port':'link',onClick(e){e.preventDefault();onClick?.(e);},children});}
 function AvatarDecoration(p){records.decoration.push(p);return jsx('span',{'data-port':'decoration',children:p.children});}
 function VerifiedBadge(p){records.badge.push(p);return jsx('span',{'data-port':'badge',children:'supplied badge'});}
 function RelativeTime(p){records.time.push(p);return jsx('time',{children:String(p.timestamp)});}
 function RichText(p){records.rich.push(p);return p.content;}
 function ImagePreview(p){records.image.push(p);return jsx('span',{'data-testid':p.testId,'data-port':'image',children:'Supplied image port'});}
 function Video(p){records.video.push(p);return jsx('span',{'data-testid':p.testId,'data-port':'video',children:'Supplied video port'});}
 function ShareMenu(p){records.share.push(p);return jsx('span',{'data-port':'share',children:p.children});}
 function Comments(p){records.comments.push(p);return jsx('div',{'data-port':'comments',children:'Supplied comments '+p.parentReplyId});}
 function Icon(){return jsx('span',{'aria-hidden':true,children:'icon'});}
 const callbacks={onClick(){records.root++;},onAuthorClick(){records.author++;}};
 const Owner=createCalloutCard({jsx,jsxs,Fragment,useMemoCache,useState,useRef,useEffect,useTranslation:()=>({t}),classNames:(...xs)=>xs.filter(Boolean).join(' '),profileRoute:address=>address?'/profile/'+address:null,
  Avatar,ProfileHover,ProfileLink,Link,AvatarDecoration,useDecorationKey(value){records.keys.push(value);return value;},VerifiedBadge,RelativeTime,RichText,ImagePreview,Video,ShareMenu,
  useReplyLike(input){records.like.push(input);return{isLiked:input.likedByViewer??false,likeCount:input.likeCount??0,toggle(){records.toggle++;}};},Comments,useIpfsPrefix(){records.prefix.push(true);return{ipfsPrefix:'synthetic-prefix'};},formatCount:value=>String(value),ShareIcon:Icon,OutlineHeart:Icon,FilledHeart:Icon,CommentIcon:Icon,ResizeObserver});
 return{Owner,records,callbacks};
}
