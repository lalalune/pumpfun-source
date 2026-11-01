#![no_std]
#![feature(link_llvm_intrinsics)]
extern "C"{#[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(seq:u32,v:u64)->u64; #[link_name="llvm.bpf.passthrough.i1.i1"]fn pt1(seq:u32,v:bool)->bool; #[link_name="llvm.bpf.passthrough.i8.i8"]fn pt8(seq:u32,v:u8)->u8; #[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;}
extern "C" { fn g(x: u64) -> u64; fn h(x: u64) -> u64; fn k(x: u64) -> u64; fn rd(p:*const u64); }
// A. InstCombine phi split: a constant tag phi with an i64 user and a compare user
#[no_mangle] pub fn a0(a:u64,b:u64,out:&mut u64)->u64{let tag:u64=if a==1{if b>5{unsafe{g(1)};1}else{0}}else{0};*out=tag;if tag!=0{unsafe{h(2)}}else{0}}
#[no_mangle] pub fn a1(a:u64,b:u64,out:&mut u64)->u64{let tag:u64=if a==1{if b>5{unsafe{g(1)};1}else{0}}else{0};let tag=unsafe{pt64(1,tag)};*out=tag;if tag!=0{unsafe{h(2)}}else{0}}
// B. select formation / SimplifyCFG speculation
#[no_mangle] pub fn b0(c:bool,a:u64,b:u64)->u64{let x=if c{a+7}else{b};unsafe{g(x)}}
#[no_mangle] pub fn b1(c:bool,a:u64,b:u64)->u64{let x=if c{unsafe{pt64(2,a+7)}}else{b};unsafe{g(x)}}
// C. Option<bool> == Some(true) read from memory
#[no_mangle] pub fn c0(o:&Option<bool>)->u64{if *o==Some(true){unsafe{g(1)}}else{unsafe{h(2)}}}
#[no_mangle] pub fn c1(o:&Option<bool>)->u64{if unsafe{pt8(3,core::mem::transmute::<Option<bool>,u8>(*o))}==1{unsafe{g(1)}}else{unsafe{h(2)}}}
// D. zext of a bool select (InstCombine)
#[no_mangle] pub fn d0(c:bool,out:&mut u64){*out=if c{1}else{0};}
#[no_mangle] pub fn d1(c:bool,out:&mut u64){*out=unsafe{pt64(4,if c{1}else{0})};}
// E. GVN load-load forwarding across a readonly-safe point
#[no_mangle] pub fn e0(p:&u64)->u64{let a=*p;let x=unsafe{g(a)};let b=*p;x+b}
#[no_mangle] pub fn e1(p:&u64)->u64{let a=*p;let x=unsafe{g(a)};let q=unsafe{ptp(5,p as *const u64 as *const u8)} as *const u64;let b=unsafe{*q};x+b}
// F. GVN store-to-load forwarding
#[no_mangle] pub fn f0(p:&mut u64,v:u64)->u64{*p=v;unsafe{rd(p)};*p+1}
#[no_mangle] pub fn f1(p:&mut u64,v:u64)->u64{*p=v;unsafe{rd(p)};(unsafe{*(ptp(6,p as *const u64 as *const u8) as *const u64)})+1}
// G. GVN PRE: a load available on one arm only
#[no_mangle] pub fn g0(c:bool,p:&u64)->u64{let mut s=0;if c{s=unsafe{g(*p)};}s+*p}
#[no_mangle] pub fn g1(c:bool,p:&u64)->u64{let mut s=0;if c{s=unsafe{g(*p)};}s+unsafe{*(ptp(7,p as *const u64 as *const u8) as *const u64)}}
// H. jump threading of a bool phi (MIR JumpThreading + LLVM JumpThreading)
#[no_mangle] pub fn h0(x:u64,y:u64)->u64{let c=if x==5{unsafe{g(x)};true}else{y==7};if c{unsafe{k(x)}}else{0}}
#[no_mangle] pub fn h1(x:u64,y:u64)->u64{let c=if x==5{unsafe{g(x)};true}else{y==7};if unsafe{pt1(8,c)}{unsafe{k(x)}}else{0}}
// I. CSE of two identical passthroughs (same seq) vs distinct seq
#[no_mangle] pub fn i0(x:u64)->u64{let a=unsafe{pt64(9,x)};let b=unsafe{pt64(9,x)};(unsafe{g(a)})+unsafe{h(b)}}
#[no_mangle] pub fn i1(x:u64)->u64{let a=unsafe{pt64(10,x)};let b=unsafe{pt64(11,x)};(unsafe{g(a)})+unsafe{h(b)}}
// J. sinking: pt computed early, used in one arm only
#[no_mangle] pub fn j0(c:bool,x:u64)->u64{let a=x*3;if c{unsafe{g(a)}}else{0}}
#[no_mangle] pub fn j1(c:bool,x:u64)->u64{let a=unsafe{pt64(12,x*3)};if c{unsafe{g(a)}}else{0}}
