#![no_std]
#![allow(unused, improper_ctypes)]
#[derive(Clone,Copy,PartialEq,Eq,Default)] #[repr(transparent)] pub struct Pk(pub [u8;32]);
pub enum Er { A(&'static u64), B(&'static u32) }
extern "C" { fn ext(); fn cpi(x:*const Option<Pk>)->u64; fn sink(x:*const Pk); fn mk(c:u32)->Er; }
#[inline(never)] fn dummy(){}
#[no_mangle] pub fn exec(new: Option<Pk>, holder: bool, shared: bool, hk:&Pk, sk:&Pk, creator:&Pk) -> Result<u32,Er> {
   let args = &(new,);
   unsafe{ext()};
   let mut target = if holder { if new.is_some() {return Err(unsafe{mk(9)})} *hk } else {
     let t = match new { Some(t)=>t, None=> return Err(unsafe{mk(1)}) };
     if t == Pk::default() { return Err(unsafe{mk(2)}) }
     if t == *hk || t == *sk { return Err(unsafe{mk(3)}) }
     t };
   let mut su: Option<Option<Pk>> = None;
   if shared { if holder { su = Some(None) } else { su = Some(args.0); target = *creator; } }
   let (target, su) = Ok::<_,Er>((target, su))?;
   unsafe{ext()};
   match su { Some(val) => { if unsafe{cpi(&val)}!=0 { return Err(unsafe{mk(5)}) } }, None => {} }
   unsafe{sink(&target)};
   Ok(0)
}
