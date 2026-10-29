import React, { useState, useEffect } from '../../packages/frontend/node_modules/react/index.js';
import { flushSync } from '../../packages/frontend/node_modules/react-dom/index.js';
import { createRoot } from '../../packages/frontend/node_modules/react-dom/client.js';
import { c as useMemoCache } from '../../packages/frontend/node_modules/react/compiler-runtime.js';
import { jsx } from '../../packages/frontend/node_modules/react/jsx-runtime.js';
import { createAvatarWorkflow } from '../../reconstruction/avatar-workflow/client.mjs';
// Diagnostic host port delegates actual React hooks unchanged and only records order.
const sourceEvents=[];
const ReactPort={useState(initial){const [value,set]=useState(initial);sourceEvents.push({type:'state-render',value});return [value,next=>{sourceEvents.push({type:'state-request',value:next});set(next);}];},
 useEffect(effect,deps){return useEffect(()=>{sourceEvents.push({type:'source-effect',deps:[...deps]});return effect();},deps);}};
const Avatar=createAvatarWorkflow({React:ReactPort,jsx,useMemoCache,classNames:(...xs)=>xs.filter(Boolean).join(' ')});
const data=(color,width,height)=>'data:image/svg+xml,'+encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><rect width="${width}" height="${height}" fill="${color}"/></svg>`);
const images={a:data('teal',40,20),b:data('purple',20,10),invalid:'data:image/png;base64,broken'};
let root,update,commits=0,forwarded=null;const errors=[],violations=[];
document.addEventListener('securitypolicyviolation',e=>violations.push({directive:e.effectiveDirective,blockedURI:e.blockedURI}));
function App({initial}) {
 const [props,setProps]=useState(initial);update=setProps;useEffect(()=>{commits++;});
 return jsx(Avatar,{address:'synthetic-address-A',src:images.a,width:36,height:36,alt:'Synthetic reply avatar',className:'authored-class',
  'data-testid':'source-avatar',
  onError:e=>{const error={src:e.currentTarget.getAttribute('src'),resolved:e.currentTarget.src,event:e.nativeEvent.type};errors.push(error);sourceEvents.push({type:'native-error',...error});},...props});
}
window.avatarHarness={images,forwardRef:node=>{forwarded=node;},mount(initial={}){root=createRoot(document.getElementById('root'));root.render(jsx(App,{initial}));},
 props(patch){flushSync(()=>update(old=>({...old,...patch})));},unmount(){root.unmount();},
 state(){return {ready:!!update,commits,sourceEvents:[...sourceEvents],errors:[...errors],violations:[...violations],forwardedTag:forwarded?.tagName??null,
  images:[...document.querySelectorAll('#root img')].map(i=>({src:i.getAttribute('src'),alt:i.alt,width:i.width,height:i.height,loading:i.loading})),
  childCount:document.getElementById('root').childElementCount};}};
window.avatarHarness.mount();
