# Source realisations of beam cells (exact single-occurrence edits, line count kept).
LIBF='#[path="admin_set_idl_authority.rs"]pub mod idl_authority;'
GLL=('lib',LIBF,'#![feature(link_llvm_intrinsics)]'+LIBF)
EXT=('cto','impl Id for Amm{fn id()->Pubkey{AMM}}\n\n#[derive(Accounts)]','impl Id for Amm{fn id()->Pubkey{AMM}}\nextern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;}/*shim: branch-weight hint decl*/\n#[derive(Accounts)]')
POOL='let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
A=('cto',POOL,'let pool_updated=!a.pool.data_is_empty() && unsafe{core::ptr::read_volatile(&a.pool)}/*shim: reload the pool account ref for the owner test*/.owner==&AMM;')
ARM='else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}'
Bf=('cto',ARM,'else{core::hint::black_box(());/*shim: memory fence at the shared non-holder arm head*/sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}')
Bv=('cto',ARM,'else{sharing_update=Some(args.0);target=unsafe{&**core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const *const Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;(false,true)}')
C=('cto','cashback:a.bonding_curve.is_cashback_coin,','cashback:unsafe{core::ptr::read_volatile(&a.bonding_curve.is_cashback_coin)}/*shim: pins the cashback byte load*/,')
D=('cto','holder_enabled:a.global.is_holder_reward_enabled}','holder_enabled:unsafe{core::ptr::read_volatile(&a.global.is_holder_reward_enabled)}/*shim: pins the holder-enabled byte load*/}')
Q=('cto','let q=a.bonding_curve.quote_mint;q==Pubkey::default()||','let q=a.bonding_curve.quote_mint;unsafe{expect(q==Pubkey::default(),false)}/*shim: default-quote test cold*/||')
OWN=('cto','CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,','CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:unsafe{core::ptr::read_volatile(&x.owner)}/*shim: pins the sweep program-clone owner load*/,key:x.key,')
V={
 'sA':[A], 'sBf':[Bf], 'sBv':[Bv], 'sC':[C], 'sD':[D], 'sQ':[GLL,EXT,Q],
 'sABf':[A,Bf], 'sABv':[A,Bv], 'sAC':[A,C], 'sAD':[A,D],
 'sABfO':[A,Bf,OWN],
}
