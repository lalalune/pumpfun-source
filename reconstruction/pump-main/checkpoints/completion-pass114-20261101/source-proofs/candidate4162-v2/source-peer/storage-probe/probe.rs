#![feature(link_llvm_intrinsics)]
extern crate anchor_lang;
use anchor_lang::prelude::*;
use core::mem::{MaybeUninit,size_of,align_of,needs_drop};
const _: [();72]=[();size_of::<MaybeUninit<[u64;9]>>()];
const _: [();8]=[();align_of::<MaybeUninit<[u64;9]>>()];
const _: [();32]=[();size_of::<Pubkey>()];
const _: [();8]=[();size_of::<*const AccountInfo>()];
const _: [();8]=[();align_of::<*const AccountInfo>()];
const _: [();16]=[();size_of::<[&[&[u8]];1]>()];
const _: [();8]=[();align_of::<[&[&[u8]];1]>()];
const _: [();0]=[();needs_drop::<MaybeUninit<[u64;9]>>() as usize];
const _: [();1]=[();((4*8>=32)&&(4*8+16<=6*8)&&(6*8+8<=7*8)&&(7*8+8<=8*8)&&(8*8+1<=72)) as usize];
extern "C"{fn observe_accounts(p:*const AccountInfo);fn observe_signers(p:*const &[&[u8]],count:usize);}
#[no_mangle]pub fn low_byte_false()->u8{let x=0u64;unsafe{core::ptr::read_volatile(&x as *const u64 as *const u8)}}
#[no_mangle]pub fn low_byte_true()->u8{let x=1u64;unsafe{core::ptr::read_volatile(&x as *const u64 as *const u8)}}
#[no_mangle]pub fn scratch_slots<'a>(key:Pubkey,accounts:&AccountInfo<'a>,cashback:bool,coin_empty:bool,bump:u8)->(Pubkey,bool){
let mut hkx=MaybeUninit::<[u64;9]>::uninit();let hkb=hkx.as_mut_ptr().cast::<u64>();
let holder_key:&Pubkey=unsafe{hkb.cast::<Pubkey>().write(key);&*hkb.cast::<Pubkey>()};
unsafe{let p=hkb.add(8).cast::<bool>();for _ in 0..6{core::ptr::write_volatile(p,coin_empty)}};
{let inner:&[&[u8]]=&[b"__event_authority",&[bump]];let es=unsafe{hkb.add(4)}.cast::<[&[&[u8]];1]>();unsafe{es.write([inner]);observe_signers((&*es).as_ptr(),1)}};
unsafe{core::ptr::write_volatile(hkb.add(6).cast::<*const AccountInfo>(),accounts as *const AccountInfo)};
// This observer represents the synchronous sweep/CPI boundary, which receives account data, not ownership of hkx or accounts.
unsafe{observe_accounts(accounts)};
unsafe{core::ptr::write_volatile(hkb.add(7),cashback as u64)};
let a1=unsafe{&*core::ptr::read_volatile(hkb.add(6).cast::<*const AccountInfo>())};
unsafe{observe_accounts(a1)};
let mut curve_cashback=false;unsafe{core::ptr::addr_of_mut!(curve_cashback).cast::<u8>().write(core::ptr::read_volatile(hkb.add(7).cast::<u8>()))};
unsafe{let p=hkb.add(8).cast::<u8>();core::ptr::write_volatile(p,bump);core::ptr::write_volatile(p,bump)};
(*holder_key,curve_cashback)
}
