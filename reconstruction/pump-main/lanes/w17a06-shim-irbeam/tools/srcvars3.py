# Beam cell vl:execute:29769 (+2,+16) + vl:execute:28873 (-1,-16) on main d4dfb04 (M 2258): source forms.
POOL='let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
A1=('cto',POOL,'let pool_updated=!a.pool.data_is_empty() && unsafe{core::ptr::read_volatile(&ctx.accounts as *const &mut AdminCto as *const &AdminCto)}/*shim: reload the accounts pointer for the pool owner test*/.pool.owner==&AMM;')
A2=('cto',POOL,'let pool_updated=!a.pool.data_is_empty() && unsafe{&*core::ptr::read_volatile(&ctx.accounts as *const &mut AdminCto as *const *const AdminCto)}/*shim: reload the accounts pointer for the pool owner test*/.pool.owner==&AMM;')
ARM='else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}'
B1=('cto',ARM,'else{sharing_update=Some(args.0);target=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;(false,true)}')
B2=('cto',ARM,'else{sharing_update=Some(args.0);target=unsafe{&**core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const *const Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;(false,true)}')
V={'kA1':[A1],'kA1B1':[A1,B1],'kA2B2':[A2,B2],'kA1B2':[A1,B2]}
A3=('cto',POOL,'let pool_updated=!a.pool.data_is_empty() && unsafe{core::ptr::read_volatile(a as *const &mut AdminCto as *const &AdminCto)}/*shim: reload the accounts pointer for the pool owner test*/.pool.owner==&AMM;')
V.update({'kA3':[A3],'kA3B1':[A3,B1],'kA3B2':[A3,B2]})
A4=('cto',POOL,'let pool_updated=!a.pool.data_is_empty() && unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for the pool owner test*/.pool.owner==&AMM;')
V.update({'kA4':[A4],'kA4B1':[A4,B1],'kA4B2':[A4,B2]})

V.update({'q0':[],'qA4':[A4],'qA4B1':[A4,B1]})
