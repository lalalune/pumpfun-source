SH_TGT='target=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;'
VARIANTS={
 # pt on the accounts pointer that the shared non-holder arm's curve-box reload derefs (IR cell pt:execute:29037, +2 M -8 B)
 'sA':[(339,SH_TGT,'target=unsafe{core::ptr::read_volatile(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer; passthrough on the accounts pointer it derefs*/.creator;')],
}
L296=' if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'
L298=' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
L306='  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
def C1P(p,m306=True,ptw=True):
    cond='expect_p(pt1(2,holder),true,%s)'%p if ptw else 'pt1(2,expect_p(holder,true,%s))'%p
    g=[(296,L296,' let target=if unsafe{%s}/*shim: target split on an opaque holder (no LLVM JumpThreading of the hr path), P(holder) %s*/{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'%(cond,p)),
       (298,L298,'  if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')]
    if m306: g.append((306,L306,'  let t=match new{None=>return Err(error!(PumpError::CtoNewCreatorRequired)),Some(t)=>t};'))
    return g
for p in ('0.49','0.48','0.5','0.45'):
    VARIANTS['c1p_'+p[2:]]=C1P(p)
    VARIANTS['c1pi_'+p[2:]]=C1P(p,False)
L298B=' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
SB=(298,L298B,' let target=if holder{if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{')
SC=(312,'if unsafe{expect_p(t==*sharing,true,0.625)}','if unsafe{expect_p(pt1(4,t==*sharing),true,0.625)}')
SD=(339,'||q==anchor_spl::token::spl_token::native_mint::ID||','||unsafe{pt1(5,q==anchor_spl::token::spl_token::native_mint::ID)}/*shim: passthrough on the native-quote compare*/||')
VARIANTS['sB']=VARIANTS['sA']+[SB]
VARIANTS['sC']=VARIANTS['sA']+[SC]
VARIANTS['sD']=VARIANTS['sA']+[SD]
W1=(578,'if coin_present&do_coin{','if coin_present&unsafe{core::mem::transmute::<u8,bool>(pt8(6,core::mem::transmute::<bool,u8>(do_coin)))}/*shim: passthrough on the do_coin byte at the AMM collect test*/{')
W2=(578,'if coin_present&do_coin{','if coin_present&unsafe{pt1(6,do_coin)}/*shim: passthrough on do_coin at the AMM collect test*/{')
T1=(659,'rent_epoch:x.rent_epoch,executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer}},crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2','rent_epoch:x.rent_epoch,executable:unsafe{pt1(7,x.executable)}/*shim: passthrough on the TCF program-clone executable byte*/,is_writable:x.is_writable,is_signer:x.is_signer}},crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2')
VARIANTS['w1']=[W1]
VARIANTS['w2']=[W2]
VARIANTS['t1']=[T1]
VARIANTS['w1t1']=[W1,T1]
VARIANTS['w2t1']=[W2,T1]
W3=(578,'if coin_present&do_coin{','if coin_present&((unsafe{pt8(6,do_coin as u8)}&1)!=0)/*shim: passthrough on the do_coin byte at the AMM collect test*/{')
W4=(578,'if coin_present&do_coin{','if coin_present&(unsafe{pt8(6,do_coin as u8)}!=0)/*shim: passthrough on the do_coin byte at the AMM collect test*/{')
W5=(578,'if coin_present&do_coin{','if coin_present&((unsafe{pt8(6,*(&do_coin as *const bool as *const u8))}&1)!=0)/*shim: passthrough on the do_coin byte at the AMM collect test*/{')
VARIANTS['w3']=[W3]
VARIANTS['w4']=[W4]
VARIANTS['w5']=[W5]
VARIANTS['w5t1']=[W5,T1]
VARIANTS['q4']=VARIANTS['sB']+[W5,T1]
