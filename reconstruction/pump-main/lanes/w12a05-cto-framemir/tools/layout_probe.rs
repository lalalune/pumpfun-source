#![allow(dead_code)]
#[derive(Clone,Copy)] pub struct P(pub [u8;32]);
pub struct AE([u8;100]); pub struct PE([u8;50]);
pub enum E { A(Box<AE>), B(Box<PE>) }
macro_rules! probe { ($name:expr, $t:ty, $ok:expr, |$r:ident| $pk:expr) => {{
  let r: Result<$t,E> = Ok($ok); let base=&r as *const _ as usize;
  let poff = match &r { Ok(x) => { let $r = x; ($pk as *const P as usize) - base }, Err(_) => 0 };
  let r2: Result<$t,E> = Err(E::A(Box::new(AE([0;100])))); let b2=&r2 as *const _ as usize;
  let eoff = match &r2 { Err(e) => (e as *const E as usize) - b2, Ok(_) => 999 };
  println!("{:<55} size {:>3}  pubkey@{:>2}  err@[{},{})  boxptr@[{},{})  overlap_pubkey_rel={:?}", $name, std::mem::size_of::<Result<$t,E>>(), poff, eoff, eoff+16, eoff+8, eoff+16,
    { let (a,b)=(eoff as isize - poff as isize, eoff as isize+16-poff as isize); if b<=0 || a>=32 {String::from("none")} else {format!("[{},{})",a.max(0),b.min(32))} });
}}}
fn main(){
 let p=P([0xab;32]);
 probe!("Pubkey", P, p, |x| x);
 probe!("(P,Option<u64>)", (P,Option<u64>), (p,Some(5)), |x| &x.0);
 probe!("(Option<u64>,P)", (Option<u64>,P), (Some(5),p), |x| &x.1);
 probe!("(P,u64)", (P,u64), (p,5), |x| &x.0);
 probe!("(P,bool)", (P,bool), (p,true), |x| &x.0);
 probe!("(P,Option<u64>,bool)", (P,Option<u64>,bool), (p,Some(5),true), |x| &x.0);
 probe!("(P,u64,bool)", (P,u64,bool), (p,5,true), |x| &x.0);
 probe!("(u64,P,bool)", (u64,P,bool), (5,p,true), |x| &x.1);
 probe!("(P,Option<Option<P>>)", (P,Option<Option<P>>), (p,None), |x| &x.0);
 probe!("(bool,bool,P,Option<Option<P>>,bool)", (bool,bool,P,Option<Option<P>>,bool), (true,true,p,None,true), |x| &x.2);
 probe!("(bool,bool,P,Option<u64>,Option<Option<P>>,bool)", (bool,bool,P,Option<u64>,Option<Option<P>>,bool), (true,true,p,Some(5),None,true), |x| &x.2);
 probe!("(P,Option<Option<P>>,Option<u64>)", (P,Option<Option<P>>,Option<u64>), (p,None,Some(5)), |x| &x.0);
 probe!("(bool,P,Option<u64>)", (bool,P,Option<u64>), (true,p,Some(5)), |x| &x.1);
 probe!("(P,Option<u64>,Option<Option<P>>)", (P,Option<u64>,Option<Option<P>>), (p,Some(5),None), |x| &x.0);
 probe!("(P,Option<u64>,bool,bool)", (P,Option<u64>,bool,bool), (p,Some(5),true,true), |x| &x.0);
 probe!("(bool,bool,P,bool,Option<u64>)", (bool,bool,P,bool,Option<u64>), (true,true,p,true,Some(5)), |x| &x.2);
 probe!("(P,usize)", (P,usize), (p,5), |x| &x.0);
 probe!("(P,&u8)", (P,&'static u8), (p,&7), |x| &x.0);
 probe!("(P,Option<P>)", (P,Option<P>), (p,None), |x| &x.0);
 probe!("(Option<P>,P)", (Option<P>,P), (None,p), |x| &x.1);
 probe!("(P,P)", (P,P), (p,p), |x| &x.0);
 probe!("(P,u8)", (P,u8), (p,7), |x| &x.0);
 probe!("Option<P> payload as (u64?)", (u64,Option<P>), (5,Some(p)), |x| match &x.1 {Some(q)=>q,None=>&p});
}
