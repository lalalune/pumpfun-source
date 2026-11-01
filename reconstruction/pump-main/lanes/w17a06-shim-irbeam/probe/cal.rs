#![no_std]
#![feature(core_intrinsics, link_llvm_intrinsics)]
#![allow(internal_features)]
pub struct S { pub a: u64, pub b: [u8;32], pub c: bool, pub d: u64 }
extern "C" { fn g(x: u64) -> u64; fn h(x: u64) -> u64; }
extern "C" { #[link_name="llvm.expect.i1"] fn expect(b: bool, v: bool) -> bool; }
// p01 plain field read (reference)
#[no_mangle] pub fn p01(s:&S)->u64{ if s.a>5 {unsafe{g(s.a)}} else {unsafe{h(s.a)}} }
// p02 read_volatile of a field
#[no_mangle] pub fn p02(s:&S)->u64{ if unsafe{core::ptr::read_volatile(&s.a)}>5 {unsafe{g(s.a)}} else {unsafe{h(s.a)}} }
// p03 read_volatile of a local
#[no_mangle] pub fn p03(s:&S)->u64{ let x=s.a+1; if unsafe{core::ptr::read_volatile(&x)}>5 {unsafe{g(x)}} else {0} }
// p04 read_volatile of a pointer param (whole 32 B key)
#[no_mangle] pub fn p04(k:&[u8;32], t:&[u8;32])->bool{ *t==unsafe{core::ptr::read_volatile(k)} }
// p05 unused volatile u8 read (placeholder form)
#[no_mangle] pub fn p05(k:&[u8;32],s:&S)->u64{ unsafe{core::ptr::read_volatile(k as *const [u8;32] as *const u8)}; s.a }
// p06 black_box of a value
#[no_mangle] pub fn p06(s:&S)->u64{ core::hint::black_box(s.a) }
// p07 black_box of a reference
#[no_mangle] pub fn p07(s:&S)->u64{ *core::hint::black_box(&s.a) }
// p08 unreachable_unchecked in an impossible arm
#[no_mangle] pub fn p08(x:u64)->u64{ match x&3 { 0=>unsafe{g(1)}, 1=>unsafe{h(2)}, 2=>unsafe{g(3)}, _=>unsafe{core::hint::unreachable_unchecked()} } }
// p09 if !c {unreachable_unchecked()} as assume
#[no_mangle] pub fn p09(x:u64)->u64{ if !(x<10){unsafe{core::hint::unreachable_unchecked()}} if x<20 {unsafe{g(x)}} else {unsafe{h(x)}} }
// p10 core::intrinsics::likely
#[no_mangle] pub fn p10(x:u64)->u64{ if core::intrinsics::likely(x==3) {unsafe{g(x)}} else {unsafe{h(x)}} }
// p11 core::intrinsics::unlikely
#[no_mangle] pub fn p11(x:u64)->u64{ if core::intrinsics::unlikely(x==4) {unsafe{g(x)}} else {unsafe{h(x)}} }
// p12 core::intrinsics::assume
#[no_mangle] pub fn p12(x:u64)->u64{ unsafe{core::intrinsics::assume(x<10)}; if x<20 {unsafe{g(x)}} else {unsafe{h(x)}} }
// p13 extern llvm.expect.i1
#[no_mangle] pub fn p13(x:u64)->u64{ if unsafe{expect(x==6,false)} {unsafe{g(x)}} else {unsafe{h(x)}} }
// p14 &T vs *const T param
#[no_mangle] pub fn p14a(s:&S, t:&mut u64){ *t=s.a; *t+=s.a; }
#[no_mangle] pub fn p14b(s:*const S, t:&mut u64){ let s=unsafe{&*s}; *t=s.a; *t+=s.a; }
// p15 Pubkey copy forms
#[no_mangle] pub fn p15a(d:&mut S, k:&[u8;32]){ d.b=*k; }
#[no_mangle] pub fn p15b(d:&mut S, k:&[u8;32]){ unsafe{core::ptr::write(&mut d.b,*k)}; }
#[no_mangle] pub fn p15c(d:&mut S, k:&[u8;32]){ unsafe{core::ptr::copy_nonoverlapping(k,&mut d.b,1)}; }
#[no_mangle] pub fn p15d(d:&S, o:&mut [u8;32]){ *o=unsafe{core::ptr::read(&d.b)}; }
#[no_mangle] pub fn p15e(d:&S, o:&mut [u8;32]){ *o=d.b; }
// p16 MaybeUninit local
#[no_mangle] pub fn p16(s:&S)->u64{ let mut m=core::mem::MaybeUninit::<u64>::uninit(); m.write(s.a); unsafe{m.assume_init()} }
// p17 Option tag byte test (&1)
#[no_mangle] pub fn p17a(o:Option<u64>)->u64{ if let Some(v)=o {v} else {7} }
#[no_mangle] pub fn p17b(o:Option<u64>)->u64{ if unsafe{*(&o as *const Option<u64> as *const u8)}&1!=0 {unsafe{o.unwrap_unchecked()}} else {7} }
// p18 transmute Option<bool> to u8
#[no_mangle] pub fn p18a(o:Option<bool>)->bool{ o.unwrap_or(false) }
#[no_mangle] pub fn p18b(o:Option<bool>)->bool{ (unsafe{core::mem::transmute::<Option<bool>,u8>(o)})==1 }
