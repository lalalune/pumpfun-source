import test from 'node:test';
import assert from 'node:assert/strict';
import {lockBodyScroll} from '../packages/frontend/src/lib/body-scroll-lock.ts';
function body(value,priority='') {
  const declarations=new Map(['overflow-x','overflow-y'].map(key=>[key,{value,priority}]));
  const style={
    get overflow(){return declarations.get('overflow-x').value;},
    getPropertyValue(key){return declarations.get(key)?.value??'';},
    getPropertyPriority(key){return declarations.get(key==='overflow'?'overflow-x':key)?.priority??'';},
    setProperty(key,next,nextPriority=''){
      for(const axis of key==='overflow'?['overflow-x','overflow-y']:[key])declarations.set(axis,{value:next,priority:nextPriority});
    },
  };
  return {style};
}
test('scroll owners preserve important priority and independently restore replacement bodies',()=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'document');
  const first=body('clip','important'),second=body('scroll');let releaseA=()=>{},releaseB=()=>{},releaseC=()=>{};
  Object.defineProperty(globalThis,'document',{value:{body:first},writable:true,configurable:true});
  try {
    releaseA=lockBodyScroll();releaseB=lockBodyScroll();releaseA();releaseA();
    assert.equal(first.style.overflow,'hidden');
    globalThis.document.body=second;releaseC=lockBodyScroll();releaseB();
    assert.equal(first.style.overflow,'clip');assert.equal(first.style.getPropertyPriority('overflow'),'important');
    assert.equal(second.style.overflow,'hidden');releaseC();assert.equal(second.style.overflow,'scroll');
  } finally {releaseA();releaseB();releaseC();if(descriptor)Object.defineProperty(globalThis,'document',descriptor);else delete globalThis.document;}
});
