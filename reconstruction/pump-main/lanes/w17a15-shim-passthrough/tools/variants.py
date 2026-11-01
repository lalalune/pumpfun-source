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
# validate source-level passthrough screen on main 8330455 (MIR block split + opaque test)
VARIANTS['v284']=[(284,'if st.mayhem{','if unsafe{pt1(16,st.mayhem)}/*shim: passthrough on the mayhem test*/{')]
VARIANTS['v289a']=[(289,'if st.holder_reward&&!(hopt==Some(true)){','if unsafe{pt1(11,st.holder_reward)}/*shim: passthrough on the 289 hr test*/&&!(hopt==Some(true)){')]
VARIANTS['v289b']=[(289,'if st.holder_reward&&!(hopt==Some(true)){','if st.holder_reward&&!unsafe{pt1(11,hopt==Some(true))}/*shim: passthrough on the 289 holder test*/{')]
VARIANTS['v296a']=[(296,'if holder&&!st.holder_reward&&!st.holder_enabled{','if unsafe{pt1(12,holder)}/*shim: passthrough on the 296 holder test*/&&!st.holder_reward&&!st.holder_enabled{')]
VARIANTS['v296b']=[(296,'if holder&&!st.holder_reward&&!st.holder_enabled{','if holder&&!unsafe{pt1(12,st.holder_reward)}/*shim: passthrough on the 296 hr test*/&&!st.holder_enabled{')]
VARIANTS['v296c']=[(296,'if holder&&!st.holder_reward&&!st.holder_enabled{','if holder&&!st.holder_reward&&!unsafe{pt1(12,st.holder_enabled)}/*shim: passthrough on the 296 he test*/{')]
VARIANTS['v298']=[(298,' let target=if holder{',' let target=if unsafe{pt1(13,holder)}/*shim: passthrough on the target split*/{')]
VARIANTS['v314']=[(314,'let cashback=if holder{false}else{st.cashback};','let cashback=if unsafe{pt1(15,holder)}/*shim: passthrough on the cashback holder test*/{false}else{st.cashback};')]
VARIANTS['v326']=[(326,'match fee{Some(f)=>{if st.quote_locked{','match fee{Some(f)=>{if unsafe{pt1(17,st.quote_locked)}/*shim: passthrough on the 326 test*/{')]
VARIANTS['v330']=[(330,'if cashback{','if unsafe{pt1(18,cashback)}/*shim: passthrough on the 330 test*/{')]
VARIANTS['v334']=[(334,'if !st.fee_configurable{','if !unsafe{pt1(19,st.fee_configurable)}/*shim: passthrough on the 334 test*/{')]
VARIANTS['v338']=[(338,'if f==0||f>st.max_fee{','if unsafe{pt1(20,f==0)}/*shim: passthrough on the 338 zero test*/||f>st.max_fee{')]
# round 2 on main 8330455 (M 2278)
PA='unsafe{&*(ptp(%d,&**a as *const AdminCto as *const u8) as *const AdminCto)}'
X31061=(558,'let coin_present=!a.coin_creator_vault_ata.data_is_empty();','let coin_present=unsafe{pt1(22,!a.coin_creator_vault_ata.data_is_empty())}/*shim: passthrough on coin_present*/;')
X27963=(312,'if unsafe{expect_p(t==*sharing,true,0.625)}','if unsafe{expect_p((pt8(4,(t==*sharing) as u8)&1)!=0,true,0.625)}')
X28725=(339,'&&a.sharing_config.owner==&FEES&&','&&'+(PA%23)+'/*shim: passthrough on the accounts pointer of the shared owner test*/.sharing_config.owner==&FEES&&')
X28849=(339,'max_fee:a.global.max_configurable_creator_fee_bps','max_fee:'+(PA%24)+'/*shim: passthrough on the accounts pointer of max_fee*/.global.max_configurable_creator_fee_bps')
X31305=(561,'if collection_native==false||coin_present{','if unsafe{pt1(25,collection_native==false)}/*shim: passthrough on the create_idempotent native test*/||coin_present{')
L579E='program:a.pump_amm.to_account_info()}))?;}'
X31870a=(579,'crate::pump_amm::cpi::collect_coin_creator_fee(CpiContext::new(','let r=crate::pump_amm::cpi::collect_coin_creator_fee(CpiContext::new(')
X31870b=(579,L579E,'program:a.pump_amm.to_account_info()}));if unsafe{pt64(21,*(&r as *const Result<()> as *const u64))}/*shim: passthrough on the collect_coin_creator_fee Result tag word (Ok niche 2)*/!=2{return r;}}')
X31870c=(579,L579E,'program:a.pump_amm.to_account_info()}));if unsafe{pt1(21,r.is_err())}/*shim: passthrough on the collect_coin_creator_fee is_err test*/{return r;}}')
for k,v in {'x31061':[X31061],'x27963':[X27963],'x28725':[X28725],'x28849':[X28849],'x31305':[X31305],'x31870':[X31870a,X31870b],'x31870c':[X31870a,X31870c]}.items(): VARIANTS[k]=v
VARIANTS['xA']=[X31061,X27963,X28725,X28849,X31305]
VARIANTS['xB']=[X31061,X27963,X28725,X28849,X31870a,X31870b]
X28802=(339,'||q==anchor_spl::token::spl_token::native_mint::ID||','||((unsafe{pt8(5,(q==anchor_spl::token::spl_token::native_mint::ID) as u8)}&1)!=0)/*shim: passthrough on the native-quote compare byte*/||')
X318MAP=(579,L579E,'program:a.pump_amm.to_account_info()})).map_err(|e|unsafe{let t=core::mem::transmute::<anchor_lang::error::Error,(u64,*const u8)>(e);core::mem::transmute::<(u64,*const u8),anchor_lang::error::Error>((pt64(26,t.0),t.1))})/*shim: passthrough on the collect_coin_creator_fee Err tag word*/?;}')
VARIANTS['x28802']=[X28802]
VARIANTS['x318m']=[X318MAP]
VARIANTS['xC']=[X31061,X27963,X28725,X28849,X28802]
VARIANTS['xD']=[X31061,X27963,X28725,X28849,X318MAP]
# round 3 on main ac37d74 (M 2284)
X31374=(578,'if coin_present&((unsafe{pt8(6,*(&do_coin as *const bool as *const u8))}&1)!=0)','if coin_present&unsafe{pt1(27,(pt8(6,*(&do_coin as *const bool as *const u8))&1)!=0)}')
VARIANTS['yA']=[X31374,X28725,X28849,X28802]
VARIANTS['yB']=[X31374,X28725,X28849,X27963]
VARIANTS['y31374']=[X31374]
# round 4 (main 4d09af4, M 2287): lead (a) pargs/pool_updated with MIR threading blocked by a pt on the condition
PA1=(762,' if pool_updated{',' if unsafe{pt1(28,pool_updated)}/*shim: passthrough on pool_updated (no MIR jump threading of pargs into the arms)*/{')
PA2=(761,'let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for pargs*/.bonding_curve.is_holder_reward,fee);')
VARIANTS['pa1']=[PA1]
VARIANTS['pa2']=[PA1,PA2]
VARIANTS['pa3']=[PA2]
