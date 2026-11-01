#![no_std]
#![feature(link_llvm_intrinsics)]
extern "C"{
 #[link_name="llvm.assume"]fn assume(b:bool);
}
extern "C" { fn g(x: u64) -> u64; fn st(p:*mut u64); fn gb(b:bool)->u64; }
// E: equality with a later reload across a call that may write: assume makes it reuse x (x stays live across the call)
#[no_mangle] pub fn e0(p:*mut u64)->u64{let x=unsafe{*p.add(1)};unsafe{st(p)};let y=unsafe{*p.add(1)};(unsafe{g(x)})+y}
#[no_mangle] pub fn e1(p:*mut u64)->u64{let x=unsafe{*p.add(1)};unsafe{st(p)};let y=unsafe{*p.add(1)};unsafe{assume(y==x)};(unsafe{g(x)})+y}
// R: range fact drops an and-1 on a raw byte
#[no_mangle] pub fn r0(p:&u8,q:*mut u64)->u64{let b=*p;unsafe{st(q)};if (b&1)!=0{unsafe{g(1)}}else{2}}
#[no_mangle] pub fn r1(p:&u8,q:*mut u64)->u64{let b=*p;unsafe{assume(b<=1)};unsafe{st(q)};if (b&1)!=0{unsafe{g(1)}}else{2}}
// C: constant fact on a reload: assume(y==C) replaces the reload by the constant (no live-range extension)
#[no_mangle] pub fn c0(p:*mut u64)->u64{let x=unsafe{*p};if x!=0{return 7}unsafe{st(p)};let y=unsafe{*p};unsafe{g(y)}}
#[no_mangle] pub fn c1(p:*mut u64)->u64{let x=unsafe{*p};if x!=0{return 7}unsafe{st(p)};let y=unsafe{*p};unsafe{assume(y==0)};unsafe{g(y)}}
// B: bool equality (i1) between unwrap_or(false) and ==Some(true): canonicalised to xor, GVN does not substitute
#[no_mangle] pub fn b0(h:Option<bool>,q:*mut u8){let hh=h==Some(true);unsafe{st(q as *mut u64)};let u=h.unwrap_or(false);unsafe{*q=u as u8;gb(hh);}}
#[no_mangle] pub fn b1(h:Option<bool>,q:*mut u8){let hh=h==Some(true);unsafe{st(q as *mut u64)};let u=h.unwrap_or(false);unsafe{assume(u==hh)};unsafe{*q=u as u8;gb(hh);}}
// P: polarity: an assume using the positive compare flips the branch polarity (F4 mechanism)
#[no_mangle] pub fn p0(x:u8,y:bool)->u64{let h=x==1;if !h{unsafe{g(1)}}else{unsafe{g(2)}}}
#[no_mangle] pub fn p1(x:u8,y:bool)->u64{let h=x==1;unsafe{assume(!y||h)};if !h{unsafe{g(1)}}else{unsafe{g(2)}}}
// N: neutral (already-known fact)
#[no_mangle] pub fn n0(x:u64)->u64{unsafe{g(x)}}
#[no_mangle] pub fn n1(x:u64)->u64{let c=x==x;unsafe{assume(c)};unsafe{g(x)}}
