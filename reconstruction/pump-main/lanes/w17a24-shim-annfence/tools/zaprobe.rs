#![no_std]
#![feature(link_llvm_intrinsics)]
extern "C"{
 #[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(seq:u32,v:u64)->u64;
 #[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;
 #[link_name="llvm.annotation.i64.p0"]fn ann(v:u64,s:*const u8,f:*const u8,l:u32)->u64;
 #[link_name="llvm.annotation.i1.p0"]fn ann1(v:bool,s:*const u8,f:*const u8,l:u32)->bool;
 #[link_name="llvm.annotation.i8.p0"]fn ann8(v:u8,s:*const u8,f:*const u8,l:u32)->u8;
 #[link_name="llvm.ptr.annotation.p0.p0"]fn pann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8)->*const u8;
 #[link_name="llvm.sideeffect"]fn se();
}
extern "C" { fn g(x: u64) -> u64; fn h(x: u64) -> u64; fn k(p: *const u64) -> u64; fn m(p:*const u8,q:*const u8,n:u64)->i32; }
const N:*const u8=core::ptr::null();
// G: one GEP used by loads in both arms: shared address register vs per-arm folded offsets
#[no_mangle] pub fn g0(p:&[u64;8],c:bool)->u64{let q=&p[5] as *const u64;let r=unsafe{g(1)};if c{unsafe{*q+r}}else{unsafe{*q.add(1)}}}
#[no_mangle] pub fn g1(p:&[u64;8],c:bool)->u64{let q=unsafe{pann(&p[5] as *const u64 as *const u8,N,N,1,N)} as *const u64;let r=unsafe{g(1)};if c{unsafe{*q+r}}else{unsafe{*q.add(1)}}}
// P: field address passed to a callee after a call (mov+add pattern)
#[no_mangle] pub fn p0(p:&[u64;8])->u64{let q=&p[3] as *const u64;let r=unsafe{g(1)};r+unsafe{k(q)}}
#[no_mangle] pub fn p1(p:&[u64;8])->u64{let q=unsafe{pann(&p[3] as *const u64 as *const u8,N,N,1,N)} as *const u64;let r=unsafe{g(1)};r+unsafe{k(q)}}
#[no_mangle] pub fn p2(p:&[u64;8])->u64{let q=unsafe{ptp(1,&p[3] as *const u64 as *const u8)} as *const u64;let r=unsafe{g(1)};r+unsafe{k(q)}}
// E: zext of a loaded bool byte before a call, used after the call in one arm (extension sinking)
#[no_mangle] pub fn e0(p:&[u8;8],c:bool)->u64{let b=p[3] as u64;let r=unsafe{g(1)};if c{r+b}else{r}}
#[no_mangle] pub fn e1(p:&[u8;8],c:bool)->u64{let b=unsafe{ann(p[3] as u64,N,N,1)};let r=unsafe{g(1)};if c{r+b}else{r}}
// C: compare computed before a call, used as a VALUE (select) after it in one arm
#[no_mangle] pub fn c0(x:u64,y:u64,z:bool)->u64{let c=x<y;let r=unsafe{g(x)};if z{r+(c as u64)}else{r}}
#[no_mangle] pub fn c1(x:u64,y:u64,z:bool)->u64{let c=unsafe{ann1(x<y,N,N,1)};let r=unsafe{g(x)};if z{r+(c as u64)}else{r}}
#[no_mangle] pub fn c2(x:u64,y:u64,z:bool)->u64{let c=unsafe{ann((x<y) as u64,N,N,1)};let r=unsafe{g(x)};if z{r+c}else{r}}
// B: compare before a call, branch on it after (fused cmp+br); i1 annotation
#[no_mangle] pub fn b0(x:u64,y:u64)->u64{let c=x<y;let r=unsafe{g(x)};if c{r+1}else{unsafe{h(r)}}}
#[no_mangle] pub fn b1(x:u64,y:u64)->u64{let c=unsafe{ann1(x<y,N,N,1)};let r=unsafe{g(x)};if c{r+1}else{unsafe{h(r)}}}
// M: memcmp-like call whose pointer argument is a field address formed before an earlier call
#[no_mangle] pub fn mm0(p:&[u8;64],q:&[u8;32])->i32{let a=&p[8] as *const u8;let r=unsafe{g(1)};if r==0{unsafe{m(a,q.as_ptr(),32)}}else{0}}
#[no_mangle] pub fn mm1(p:&[u8;64],q:&[u8;32])->i32{let a=unsafe{pann(&p[8] as *const u8,N,N,1,N)};let r=unsafe{g(1)};if r==0{unsafe{m(a,q.as_ptr(),32)}}else{0}}
// S: sideeffect in an otherwise-empty arm (does the block survive?)
#[no_mangle] pub fn s0(x:u64,c:bool)->u64{let y=if c{x+1}else{x};unsafe{g(y)}}
#[no_mangle] pub fn s1(x:u64,c:bool)->u64{let y=if c{unsafe{se()};x+1}else{x};unsafe{g(y)}}
// U: unused ann on a load: does it keep the load before the call?
#[no_mangle] pub fn u0(p:&[u64;8],c:bool)->u64{let v=p[2];let r=unsafe{g(1)};if c{r+v}else{r}}
#[no_mangle] pub fn u1(p:&[u64;8],c:bool)->u64{let v=p[2];unsafe{ann(v,N,N,1)};let r=unsafe{g(1)};if c{r+v}else{r}}
