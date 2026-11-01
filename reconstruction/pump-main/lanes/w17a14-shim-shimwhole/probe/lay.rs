#![no_std]
#![allow(unused)]
extern crate alloc;
#[derive(Clone,Copy,PartialEq,Eq,Default)] #[repr(transparent)] pub struct Pk(pub [u8;32]);
pub struct AE{a:u64,b:[u8;100]} pub struct PE{a:u64}
pub enum Er { AnchorError(alloc::boxed::Box<AE>), ProgramError(alloc::boxed::Box<PE>) }
#[repr(C)] pub struct J{pub target:Pk,pub su:Option<Option<Pk>>,pub cashback:bool}
#[inline(never)] fn mk<T>(v:T)->T{v}
macro_rules! offs { ($name:ident, $ty:ty, $val:expr, $($f:tt),*) => {
  #[no_mangle] pub fn $name() -> [usize; 5] { let r: $ty = $val; let base=&r as *const _ as usize; let mut o=[0usize;5]; o[4]=core::mem::size_of::<$ty>(); if let Ok(ref t)=r { let mut i=0; $( o[i]=(&t.$f as *const _ as usize)-base; i+=1; )* } o } } }
offs!(res_tsc, Result<(Pk,Option<Option<Pk>>,bool),Er>, Ok((Pk([1;32]),Some(None),true)), 0,1,2);
offs!(res_j, Result<J,Er>, Ok(J{target:Pk([1;32]),su:Some(None),cashback:true}), target,su,cashback);
offs!(res_cts, Result<(bool,Pk,Option<Option<Pk>>),Er>, Ok((true,Pk([1;32]),Some(None))), 0,1,2);
#[no_mangle] pub fn tup() -> [usize;4] { let t:(Pk,Option<Option<Pk>>,bool)=(Pk([1;32]),Some(None),true); let b=&t as *const _ as usize; [(&t.0 as *const _ as usize)-b,(&t.1 as *const _ as usize)-b,(&t.2 as *const _ as usize)-b, core::mem::align_of::<Result<(Pk,Option<Option<Pk>>,bool),Er>>()] }
#[repr(C,align(8))] pub struct J8{pub target:Pk,pub su:Option<Option<Pk>>,pub cashback:bool}
offs!(res_j8, Result<J8,Er>, Ok(J8{target:Pk([1;32]),su:Some(None),cashback:true}), target,su,cashback);
offs!(res_t64, Result<(Pk,Option<Option<Pk>>,bool,u64),Er>, Ok((Pk([1;32]),Some(None),true,7u64)), 0,1,2,3);
