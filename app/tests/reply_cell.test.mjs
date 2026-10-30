import{test}from'node:test';import assert from'node:assert/strict';import{createRequire}from'node:module';import{mkdtemp,mkdir,copyFile,readFile,writeFile,rm}from'node:fs/promises';import path from'node:path';import os from'node:os';
import{jsx}from'../packages/frontend/node_modules/react/jsx-runtime.js';
import{createReplyHost,REPLY,DATA_IMAGE}from'./fixtures/reply-cell-ports.mjs';
import{APP_ROOT,DIRECTORY,verify}from'../reconstruction/reply-cell/verify.mjs';
const frontend=createRequire(new URL('../packages/frontend/package.json',import.meta.url)),{renderToStaticMarkup}=frontend('react-dom/server'),base58=createRequire(frontend.resolve('@solana/web3.js'))('bs58');
const render=(C,props)=>renderToStaticMarkup(jsx(C,props)),callout={coinMint:'synthetic-mint',calloutId:'synthetic-callout'};
test('complete96-slot owner, all providers/helpers and conditional MAIN Flight chain regenerate',async()=>{const p=await verify();assert.match(p.mainAdmission.path,/rootFlight.*mobile.*349919.*710416/);assert.equal(p.mainAdmission.elementUses.length,1);assert.equal(p.witnesses.filter(w=>w.label==='actual ordinary MAIN reply-cell invocation with full props').length,3);assert.match(p.mainAdmission.excluded,/316917/);});
test('actual MAIN descriptors keep hideActions/input quirks and callout_detail hook instrumentation',()=>{
 for(const mode of ['missingCallout','linkedCallout','unlinkedCallout']){const h=createReplyHost({base58});const html=render(h.renderers[mode],{reply:REPLY,callout});assert.match(html,/callout-reply-cell/);assert.equal(html.includes('callout-reply-like'),mode==='linkedCallout');assert.deepEqual(h.records.like[0],{mint:mode==='missingCallout'?'':callout.coinMint,calloutId:mode==='missingCallout'?'':callout.calloutId,replyId:REPLY.replyId,likeCount:2,likedByViewer:false,surface:'callout_detail'});assert.equal(h.records.mute.length,1);}
});
test('exact hook order and identity/address/username/default profile derivation are preserved',()=>{
 const h=createReplyHost({base58,verified:true});render(h.ReplyCell,{reply:REPLY,mint:'m',calloutId:'c'});assert.deepEqual(h.records.order.slice(0,7),['translation','IPFS','verified','own-hook','own-predicate','own-predicate','like-hook']);
 assert.equal(h.records.avatars[0].address,REPLY.caller.walletAddress);assert.equal(h.records.avatars[0].alt,'Display name');assert.equal(h.records.avatars[0].width,36);assert.equal(h.records.avatars[0].src,DATA_IMAGE);assert.equal(h.records.hovers.length,2);assert.equal(h.records.profileLinks[0].href,'/profile/'+REPLY.caller.walletAddress);
 assert.equal(h.records.times[0].timestamp,REPLY.createdAt);assert.equal(h.records.text[0].content,REPLY.content);
 const fallback=createReplyHost({base58});render(fallback.ReplyCell,{reply:{...REPLY,userId:'opaque / id',caller:{username:' ',displayName:' '}}});assert.equal(fallback.records.avatars[0].address,'opaque / id');assert.equal(fallback.records.profileLinks[0].href,'/profile/opaque%20%2F%20id');assert.equal(fallback.records.hovers.length,0);
});
test('undefined/null/explicit profile overrides keep wrapper and focus semantics distinct',()=>{
 for(const[replierHref,count,hover]of[[undefined,2,2],[null,0,0],['/authored-profile',2,0]]){const h=createReplyHost({base58});const html=render(h.ReplyCell,{reply:REPLY,replierHref,replierAvatarShape:'squircle',focused:true});assert.equal(h.records.profileLinks.length,count);assert.equal(h.records.hovers.length,hover);assert.match(html,/bg-white/);if(replierHref){assert.equal(h.records.profileLinks[0].profileId,'');assert.match(h.records.profileLinks[0].className,/focus-visible/);}assert.match(h.records.avatars[0].className,/rounded-xl/);}
});
test('image-admission variants and complete40px preview wrapper retain provider order/default URI query rewrite',()=>{
 const calls=[],url='https://host.invalid/ipfs/value?img-width=9&x=1';const h=createReplyHost({base58,sourceUri:{D(value,prefix){calls.push(['D',value,prefix]);return url;},d(value){calls.push(['d',value]);return true;}}});render(h.ReplyCell,{reply:{...REPLY,caller:{...REPLY.caller,avatarUrl:'  data:synthetic  '}}});
 assert.deepEqual(calls,[['D','data:synthetic','https://pump.mypinata.cloud/ipfs/'],['d',url]]);assert.equal(h.records.avatars[0].src,'https://host.invalid/ipfs/value?img-width=40&x=1&img-dpr=2&img-onerror=redirect');
 const empty=createReplyHost({base58});render(empty.ReplyCell,{reply:{...REPLY,caller:{...REPLY.caller,avatarUrl:'  '}}});assert.equal(empty.records.URI.length,0);assert.equal(empty.records.avatars[0].src,undefined);
});
test('like/share/comment callbacks preserve stop-before-call, counts, labels and full comment slot',()=>{
 const h=createReplyHost({base58,isLiked:true,likeCount:12000});let toggles=0;const html=render(h.ReplyCell,{reply:REPLY,mint:'raw/mint',calloutId:'c',commentCount:0,commentsExpanded:true,onToggleComments:()=>{h.records.order.push('comments-toggle');toggles++;},commentsSlot:jsx('div',{'data-comment-slot':'yes',children:'Supplied slot'})});
 assert.match(html,/12K/);assert.match(html,/data-comment-slot="yes"/);assert.equal(h.records.share[0].sharePath,'/callouts/raw/mint/c/'+REPLY.replyId);
 const click=id=>h.records.buttons.find(p=>p['data-testid']===id).onClick({stopPropagation(){h.records.order.push('stop');}});
 click('callout-reply-like');assert.deepEqual(h.records.order.slice(-2),['stop','like-toggle']);click('callout-reply-share');assert.equal(h.records.order.at(-1),'stop');click('callout-reply-comments-toggle');assert.deepEqual(h.records.order.slice(-2),['stop','comments-toggle']);assert.equal(toggles,1);
});
test('own-ID menu gate is independent of hideActions; no service/auth permission is inferred',()=>{
 const other=createReplyHost({base58});render(other.ReplyCell,{reply:REPLY,hideActions:true});assert.equal(other.records.mute.length,1);assert.equal(other.records.like.length,1);assert.equal(other.records.share.length,0);
 const own=createReplyHost({base58,own:new Set([REPLY.authorCcUserId])});const html=render(own.ReplyCell,{reply:REPLY});assert.equal(own.records.mute.length,0);assert.match(html,/callout-reply-like/);
});
test('metadata/media/social and count-only states keep source conditional/nullish behavior',()=>{
 const h=createReplyHost({base58});const html=render(h.ReplyCell,{reply:{...REPLY,mediaUrl:DATA_IMAGE,caller:{...REPLY.caller,twitterUrl:''}},fallbackXUsername:'fallback-x',commentCount:0});assert.equal(h.records.media[0].src,DATA_IMAGE);assert.deepEqual(h.records.social[0],{twitterUrl:'',xUsername:'fallback-x'});assert.match(html,/callout-reply-comments-count/);assert.doesNotMatch(html,/callout-reply-comments-toggle/);
 const nulls=createReplyHost({base58});render(nulls.ReplyCell,{reply:{...REPLY,likeCount:null,likedByViewer:null},commentCount:null});assert.equal(nulls.records.like[0].likeCount,0);assert.equal(nulls.records.like[0].likedByViewer,false);
});
async function fixture(t){const root=await mkdtemp(path.join(os.tmpdir(),'reply-source-'));t.after(()=>rm(root,{recursive:true,force:true}));
 for(const d of['evidence/web/objects','recovered',DIRECTORY,'reconstruction/search-navigation'])await mkdir(path.join(root,d),{recursive:true});
 const p=JSON.parse(await readFile(path.join(APP_ROOT,DIRECTORY,'PROVENANCE.json'),'utf8')),sources=new Set(p.contexts.map(c=>c.source));sources.add(p.mainAdmission.rootHTML.path);
 // Accepted navigation's existing verifier uses additional captured guard/router inputs.
 const manifest=JSON.parse(await readFile(path.join(APP_ROOT,'evidence/web/manifest.json'),'utf8'));
 const nav=JSON.parse(await readFile(path.join(APP_ROOT,'reconstruction/search-navigation/PROVENANCE.json'),'utf8'));
 const gather=v=>{if(!v||typeof v!=='object')return;for(const[k,x]of Object.entries(v))if(k==='source'&&typeof x==='string'&&x.startsWith('evidence/web/objects/'))sources.add(x);else gather(x);};gather(nav);
 for(const p of sources)await copyFile(path.join(APP_ROOT,p),path.join(root,p));for(const p of['evidence/web/manifest.json','recovered/modules.json',DIRECTORY+'/client.mjs',DIRECTORY+'/PROVENANCE.json','reconstruction/search-navigation/navigation.mjs'])await copyFile(path.join(APP_ROOT,p),path.join(root,p));return root;
}
test('a changed main-hook surface or source callback order fails exact raw derivation',async t=>{
 const root=await fixture(t),file=path.join(root,DIRECTORY,'client.mjs'),s=await readFile(file,'utf8');assert.ok(s.includes('surface: "callout_detail"'));await writeFile(file,s.replace('surface: "callout_detail"','surface: "home_feed"'));await assert.rejects(verify(root),/reply-cell editable source differs/);
});
test('dropped image variant/context and forged helper identity cannot pass source inventory pins',async t=>{
 const root=await fixture(t),file=path.join(root,'recovered/modules.json'),j=JSON.parse(await readFile(file,'utf8'));j.modules=j.modules.filter(m=>m.sha256!=='64085dc31cc9ebbcde019719b8096cfd198d84216b08826b70461fdfa689dc55');await writeFile(file,JSON.stringify(j));await assert.rejects(verify(root),/all physical variants 741084/);
});
