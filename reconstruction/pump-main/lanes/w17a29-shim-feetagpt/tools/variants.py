# w17a29 feetagpt: fee-tag phi variants on main 53ec7fb53 (line count kept; each (a,b) must occur once)
RV='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
R338='if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'
SIG=('sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);','sharing:&Pubkey,fo:&mut Option<u64>)->Result<Pubkey>{let holder=hopt==Some(true);')
DECL=('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let mut fo:Option<u64>=None;let holder=hopt==Some(true);')
CALL=('validate(&st,hopt,fee,new,holder_key,sk)?;','validate(&st,hopt,fee,new,holder_key,sk,&mut fo)?;')
TUP=('(holder,cashback,target,sharing_update,collect_old,skip)};','(holder,cashback,target,sharing_update,collect_old,skip,FOX)};')
DES=('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fo)={')
U757=('if let Some(f)=fee{curve.creator_fee_bps=f;}','if let Some(f)=fo{curve.creator_fee_bps=f;}')
UP=('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,fo);')
# helper on line 8 (no new line): pass the Option tag word through llvm.bpf.passthrough (const-generic seq)
H8A='/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/'
PTO='#[inline(always)]unsafe fn pto<const N:u32>(o:Option<u64>)->Option<u64>{let mut r=o;let p=&mut r as *mut Option<u64> as *mut u64;*p=pt64(N,*p);r}/*shim: passthrough on the Option<u64> tag word (one tag phi with both users)*/'
def fo(keep338=True,ok='Some(f)',tup='fo',helper=False,okpos='after'):
    e=[SIG,DECL,CALL,(TUP[0],TUP[1].replace('FOX',tup)),DES,U757,UP]
    if keep338:
        if okpos=='after': e.append((R338+RV+'}None=>{}}',R338+RV+'*fo='+ok+';}None=>{}}'))
        else: e.append((R338+RV+'}None=>{}}',R338+'*fo='+ok+';'+RV+'}None=>{}}'))
    else:
        e.append((R338+RV+'}None=>{}}',R338+'*fo='+ok+';}None=>{}}'))
    if helper: e.append((H8A,H8A+PTO))
    return e
OKPT='unsafe{core::mem::transmute::<[u64;2],Option<u64>>([pt64(32,1),f])}/*shim: passthrough on the OK-path fee tag constant*/'
V={
 'fo':fo(),
 'fo8':fo(keep338=False),
 'foj':fo(tup='unsafe{pto::<31>(fo)}',helper=True),
 'foj8':fo(keep338=False,tup='unsafe{pto::<31>(fo)}',helper=True),
 'foc':fo(ok=OKPT),
 'foc8':fo(keep338=False,ok=OKPT),
}
# round 2: alternative single-phi spellings (placement / RA basin probes)
U757P=('if let Some(f)=fee{curve.creator_fee_bps=f;}','if let Some(f)=unsafe{pto::<31>(fo)}/*shim: passthrough on the fee tag at the 757 test*/{curve.creator_fee_bps=f;}')
def fo2(ok='Some(f)',decl_init='None',u757=None,helper=False,okpos='after',keep338=True):
    e=fo(keep338=keep338,ok=ok,helper=helper,okpos=okpos)
    if decl_init!='None':
        e=[(a,b.replace('let mut fo:Option<u64>=None;','let mut fo:Option<u64>='+decl_init+';')) if a==DECL[0] else (a,b) for a,b in e]
    if u757: e=[u757 if a==U757[0] else (a,b) for a,b in e]
    return e
INIT0='unsafe{core::mem::transmute::<[u64;2],Option<u64>>([pt64(33,0),0])}/*shim: passthrough on the None fee tag constant*/'
V.update({
 'focb':fo2(ok=OKPT,okpos='before'),
 'fos757':fo2(u757=U757P,helper=True),
 'focs':fo2(decl_init=INIT0),
 'focsc':fo2(decl_init=INIT0,ok=OKPT),
})
# round 3: None-init passthrough with an uninit value word (no value phi; pool gets the entry fee value)
INIT0U='unsafe{core::mem::transmute::<[core::mem::MaybeUninit<u64>;2],Option<u64>>([core::mem::MaybeUninit::new(pt64(33,0)),core::mem::MaybeUninit::uninit()])}/*shim: passthrough on the None fee tag constant (value word uninit)*/'
V.update({
 'focs2':fo2(decl_init=INIT0U),
 'focsc2':fo2(decl_init=INIT0U,ok=OKPT),
 'focs28':fo2(decl_init=INIT0U,keep338=False),
 'focsc28':fo2(decl_init=INIT0U,ok=OKPT,keep338=False),
})
# round 4: + native-quote test weighted 1:2000 (beam cell bwf:execute:28810 on foc)
QN=('||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};','||(unsafe{expect(q==anchor_spl::token::spl_token::native_mint::ID,false)})/*shim: native-quote test weighted 1:2000 (keeps the sweep memcmp result out of r7 with the single fee-tag phi)*/||a.global.whitelisted_quote_mints.contains(&q)};')
V.update({
 'foce':fo(ok=OKPT)+[QN],
 'foje':fo(tup='unsafe{pto::<31>(fo)}',helper=True)+[QN],
 'm0e':[QN],
})
V.update({
 'foce8':fo(ok=OKPT,keep338=False)+[QN],
 'foje8':fo(keep338=False,tup='unsafe{pto::<31>(fo)}',helper=True)+[QN],
})
# round 5: size knobs on foje (volatile CtoState byte loads; beam cells vl:execute:28883 cashback, vl:execute:28893 holder_enabled)
VC=('cashback:a.bonding_curve.is_cashback_coin,quote_locked,','cashback:unsafe{core::ptr::read_volatile(&a.bonding_curve.is_cashback_coin)}/*shim: volatile cashback byte load (-16 B size knob)*/,quote_locked,')
VH=('holder_enabled:a.global.is_holder_reward_enabled};','holder_enabled:unsafe{core::ptr::read_volatile(&a.global.is_holder_reward_enabled)}/*shim: volatile holder_enabled byte load (-16 B size knob)*/};')
FOJE=fo(tup='unsafe{pto::<31>(fo)}',helper=True)+[QN]
V.update({
 'fj1c':FOJE+[VC],
 'fj1h':FOJE+[VH],
 'fj2':FOJE+[VC,VH],
})
# round 6: -32 B knob on foje: volatile holder_reward byte in validate (beam cell vl:validate:27664)
VR=(' if st.holder_reward&&!(hopt==Some(true)){',' if unsafe{core::ptr::read_volatile(&st.holder_reward)}/*shim: volatile holder_reward byte read in validate (-32 B size knob)*/&&!(hopt==Some(true)){')
V.update({'fv':FOJE+[VR]})
# round 7: peel main's basin-tuning volatile shims on foje (the single-phi basin may not need them)
P1=('target=unsafe{core::ptr::read_volatile(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer; passthrough on the accounts pointer it derefs*/.creator;','target=a.bonding_curve.creator;')
P2=('unsafe{core::ptr::read_volatile(curve as *const Box<Account<BondingCurve>> as *const &mut Account<BondingCurve>)}.creator=target;/*shim: reload the curve box pointer for the creator store*/','curve.creator=target;')
P3=('!unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for the pool data_is_empty test*/.pool.data_is_empty()','!a.pool.data_is_empty()')
P4=('owner:unsafe{core::ptr::read_volatile(&x.owner)}/*shim: pins the sweep program-clone owner load*/','owner:x.owner')
P5=(' unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;if st.mayhem{',' if st.mayhem{')
V.update({'fjp1':FOJE+[P1],'fjp2':FOJE+[P2],'fjp3':FOJE+[P3],'fjp4':FOJE+[P4],'fjp5':FOJE+[P5]})
# round 8: try to realise climb force 472=r2 (the sharing_config account pointer loaded for sk in the validate entry block)
SKA=('skm.as_mut_ptr().write(a.sharing_config.key());','skm.as_mut_ptr().write(unsafe{&*(ptp(25,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the sk sharing_config load*/.sharing_config.key());')
SKB=('let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}','let shared={let sk=unsafe{&*(ptp(26,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the shared sharing_config key*/.sharing_config.key();a.bonding_curve.creator==sk}')
V.update({'fjsa':FOJE+[SKA],'fjsb':FOJE+[SKB]})
