QL='let quote_locked={let q=a.bonding_curve.quote_mint;'
ST='let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled};'
VAL='validate(&st,hopt,fee,new,&holder_key,&sk)'
EARLY=('cto',QL,'let (cb0,hr0,my0)=unsafe{(core::ptr::read_volatile(&a.bonding_curve.is_cashback_coin),core::ptr::read_volatile(&a.bonding_curve.is_holder_reward),core::ptr::read_volatile(&a.bonding_curve.is_mayhem_mode))}/*shim: curve flag loads before quote_locked, orig order a3,a5,a2*/;'+QL)
WV='core::ptr::write_volatile(core::ptr::addr_of_mut!((*p).%s),%s);'
STV=('cto',ST,'let mut stu=core::mem::MaybeUninit::<CtoState>::uninit();let st=unsafe{let p=stu.as_mut_ptr();'
     +WV%('cashback','cb0')+WV%('holder_reward','hr0')+WV%('mayhem','my0')
     +'core::ptr::addr_of_mut!((*p).creator).write(a.bonding_curve.creator);'
     +WV%('quote_locked','quote_locked')+WV%('fee_configurable','a.global.creator_fee_configurable')+WV%('holder_enabled','a.global.is_holder_reward_enabled')+WV%('max_fee','a.global.max_configurable_creator_fee_bps')
     +'stu.assume_init_ref()}/*shim: orig stxb order -0xe,-0xf,-0x10 | creator | -0xd,-0xb,-0xc | max_fee*/;')
VALR=('cto',VAL,'validate(st,hopt,fee,new,&holder_key,&sk)')
V={'m1':[],'sh1':[EARLY,STV,VALR]}
# store-order shim alone (loads where main has them)
STV0=('cto',ST,STV[2].replace('cb0','a.bonding_curve.is_cashback_coin').replace('hr0','a.bonding_curve.is_holder_reward').replace('my0','a.bonding_curve.is_mayhem_mode'))
V['sh0']=[STV0,VALR]
