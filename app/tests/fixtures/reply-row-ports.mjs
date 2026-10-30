import{jsx,jsxs,Fragment}from'../../packages/frontend/node_modules/react/jsx-runtime.js';import{c as useMemoCache}from'../../packages/frontend/node_modules/react/compiler-runtime.js';
import{createOrdinaryReplyRow}from'../../reconstruction/reply-row/client.mjs';
export const IMAGE='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="purple"/></svg>');
export const ROW={reply:{replyId:'synthetic-reply',userId:'synthetic-user',content:'Synthetic reply',caller:{username:'Reply name'}},parent:null,callout:{calloutId:'synthetic-callout',coinMint:'synthetic-mint',author:{walletAddress:'synthetic-address',username:' Root name ',avatarUrl:IMAGE},createdAtMs:1793318400000,note:'Synthetic root note',mediaUrl:null}};
export function createRowHost(){const records={root:[],reply:[],quote:[],position:[],normalize:[],preview:[],labels:[],links:[],clicks:[]};const t=key=>key;
 function RootCallout(props){records.root.push(props);return jsxs('section',{'data-port':'root','data-testid':props.testId,children:[jsx('h2',{children:props.authorName}),props.nameAdornment,jsx('p',{'data-port':'root-note',children:props.note}),props.children]});}
 function ReplyCell(props){records.reply.push(props);return jsx('article',{'data-port':'reply','data-hide-actions':String(props.hideActions),'data-mint':props.mint,'data-callout':props.calloutId,children:props.reply.content});}
 function QuotePreview(props){records.quote.push(props);return jsx('blockquote',{'data-port':'quote',children:JSON.stringify(props.quoted)});}
 function CoinPosition(props){records.position.push(props);return jsx('aside',{'data-port':'position',children:'Opaque supplied position renderer'});}
 function Link({children,onClick,...props}){records.links.push(props);return jsx('a',{...props,onClick(e){e.preventDefault();records.clicks.push(props.href);onClick?.(e);},children});}
 const Owner=createOrdinaryReplyRow({jsx,jsxs,Fragment,useMemoCache,classNames:(...xs)=>xs.filter(Boolean).join(' '),useTranslation:()=>({t}),RootCallout,ReplyCell,QuotePreview,CoinPosition,Link,
 truncateAddress(value,start,end){records.labels.push({value,start,end});if(!value)return'';return value.length<=start+end+1?value:`${value.slice(0,start)}…${value.slice(-end)}`;},
 normalizeAvatarInput(value){records.normalize.push(value);return value?.trim()||undefined;},previewImage(input){records.preview.push(input);return input.sourceUrl??null;}});
 return{Owner,records};
}
