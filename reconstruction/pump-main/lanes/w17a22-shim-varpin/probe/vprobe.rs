#![no_std]
#![feature(link_llvm_intrinsics)]
extern "C"{
 #[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);
}
extern "C" { fn g(x: u64) -> u64; fn rd(p:*const u64) -> u64; fn cmp(a:*const u8,b:*const u8)->i32; fn sink(p:*const u64); }
#[inline(always)] fn pin<T>(x:&T){unsafe{vann(x as *const T as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}}
// G: forwarding across an opaque call (may write memory) vs across a readonly argmem call
#[no_mangle] pub fn g0(x:u64)->u64{let mut t=[x,x+1];t[1]=unsafe{g(t[0])};t[0]+t[1]}
#[no_mangle] pub fn g1(x:u64)->u64{let mut t=[x,x+1];pin(&t);t[1]=unsafe{g(t[0])};t[0]+t[1]}
#[no_mangle] pub fn g2(x:u64,p:&[u8;32],q:&[u8;32])->u64{let t=[x,x+1];pin(&t);let c=unsafe{cmp(p.as_ptr(),q.as_ptr())};t[0]+c as u64}
// D: DSE of an overwritten store / a never-read pinned local
#[no_mangle] pub fn d0(x:u64)->u64{let mut t=[x,0u64];pin(&t);t[0]=x+5;unsafe{g(t[0])}}
#[no_mangle] pub fn d1(x:u64)->u64{let t=[x,x+7];pin(&t);unsafe{g(x)}}
#[no_mangle] pub fn d2(x:u64)->u64{let t=[x,x+7];unsafe{g(x)};pin(&t);0}
// M: memcpy forwarding through a pinned intermediate
#[no_mangle] pub fn m0(p:&[u64;4])->u64{let t=*p;pin(&t);let u=t;unsafe{g(1)};unsafe{rd(u.as_ptr())}}
// S: stack colouring of two pinned locals with disjoint scopes
#[no_mangle] pub fn s0(x:u64)->u64{let a={let t=[x,x+1,x+2];pin(&t);unsafe{rd(t.as_ptr())}};let b={let u=[x,x+3,x+4];pin(&u);unsafe{rd(u.as_ptr())}};a+b}
#[no_mangle] pub fn s1(x:u64)->u64{let t=[x,x+1,x+2];pin(&t);let a=unsafe{g(x)};let u=[x,x+3,x+4];pin(&u);a+unsafe{g(x+1)}}
