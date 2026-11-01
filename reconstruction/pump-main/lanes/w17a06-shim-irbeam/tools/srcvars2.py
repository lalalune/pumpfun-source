# Source realisations of the beam cells on main 287d331/d4dfb04 (w17a02+w17a03+w17a04 shims landed).
POOL='let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
A=('cto',POOL,'let pool_updated=!a.pool.data_is_empty() && unsafe{core::ptr::read_volatile(&a.pool)}/*shim: reload the pool account ref for the owner test*/.owner==&AMM;')
ARM='else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}'
Bf=('cto',ARM,'else{core::hint::black_box(());/*shim: memory fence at the shared non-holder arm head*/sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}')
Bv=('cto',ARM,'else{sharing_update=Some(args.0);target=unsafe{&**core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const *const Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;(false,true)}')
COIN='let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;'
W=('cto',COIN,'let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{core::hint::black_box(());/*shim: memory fence on the no-coin arm*/false};')
W0=('cto',COIN,'let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};')
V={'n0':[],'nA':[A],'nBf':[Bf],'nBv':[Bv],'nW':[W],'nW0':[W0],'nABf':[A,Bf],'nABfW':[A,Bf,W],'nABvW':[A,Bv,W],'nAW':[A,W]}
