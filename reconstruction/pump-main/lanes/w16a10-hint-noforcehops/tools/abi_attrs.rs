// ABI-attribute probe for site (a), not built into any program. Reproduce with the identity rustc:
//   ~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/bin/rustc --edition 2021 --crate-type=lib -O --emit=llvm-ir -o t.ll abi_attrs.rs
//   grep '^define' t.ll
use std::rc::Rc; use std::cell::RefCell;
pub struct Info<'a>{pub key:&'a [u8;32],pub lamports:Rc<RefCell<&'a mut u64>>,pub data:Rc<RefCell<&'a mut [u8]>>,pub owner:&'a [u8;32],pub rent_epoch:u64,pub is_signer:bool,pub is_writable:bool,pub executable:bool}
#[derive(Clone)] pub struct Signer<'info>{info:&'info Info<'info>}
#[inline(never)] pub fn by_ref(p:&Info)->u64{p.rent_epoch}
#[inline(never)] pub fn by_signer_val(p:Signer)->u64{p.info.rent_epoch}
#[inline(never)] pub fn by_opt(p:Option<&Info>)->u64{p.map(|x|x.rent_epoch).unwrap_or(0)}
#[inline(never)] pub fn by_pair(p:(&Info,&Info))->u64{p.0.rent_epoch+p.1.rent_epoch}
#[inline(never)] pub fn by_raw(p:*const Info)->u64{unsafe{(*p).rent_epoch}}
#[inline(never)] pub fn by_cell(p:&std::cell::Cell<u64>)->u64{p.get()}
