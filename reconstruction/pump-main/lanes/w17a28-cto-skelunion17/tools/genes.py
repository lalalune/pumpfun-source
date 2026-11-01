# w17a28 skelunion17 genes on main 53ec7fb53 (admin_cto.rs text). Each gene is a list of callables s->s.
# Exact single-occurrence edits, line count kept (asserted by the driver). Experiment only.
def one(s, a, b):
    c = s.count(a)
    assert c == 1, (c, a[:140])
    return s.replace(a, b)

def E(a, b):
    return lambda s: one(s, a, b)

G = {}
# ---- k8 (w17a09/w17a20/w17a25): PDA block ahead of the shared test (statement reorder only)
def _k8(s):
    i = s.index('let shared={let ')
    j = s.index('let mut hkx=', i)
    k = s.index('let quote_locked=', j)
    return s[:i] + s[j:k] + s[i:j] + s[k:]
G['K8'] = [_k8]

# ---- s_nat1 (w17a21): native tail returns Ok(amount) after `?` on transfer_native (original's sweep-exit join shape)
L664 = '   (if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{'
NATQ = '   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)?;}Ok(amount)}else{'
G['NAT'] = [E(L664, NATQ)]

# ---- n1 (w17a13 m2n): event reads creator_fee_bps directly (no nf local)
G['N1'] = [E('let nf=a.bonding_curve.creator_fee_bps;', ''),
           E(',new_creator_fee_bps:nf,', ',new_creator_fee_bps:a.bonding_curve.creator_fee_bps,')]

# ---- holder late (w17a20 hl, source form): holder/cashback computed after validate (orig: after the mayhem test)
HC = 'let holder=hopt==Some(true);let cashback=!holder&&st.cashback;'
def _hl(s):
    s = one(s, HC, '')
    a = 'validate(&st,hopt,fee,new,holder_key,sk)?;' if 'validate(&st,hopt,fee,new,holder_key,sk)?;' in s else None
    if a is None:
        import re
        m = re.search(r'validate\((?:&)?st,hopt,fee,new,holder_key,sk(?:,&mut hf)?\)\?;', s)
        a = m.group(0)
    return one(s, a, a + HC)
G['HL'] = [_hl]

# ---- ve1n source form sh1h2 (w17a20), ported: global bound early, curve flags read early, CtoState written field by field
QL = 'let quote_locked={let q=a.bonding_curve.quote_mint;(unsafe{expect(q==Pubkey::default(),false)})/*shim: default-quote test weighted 1:2000*/||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
G2 = 'let g:&Account<Global>=&a.global;'
EF2 = 'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'
QLG = QL.replace('a.global.whitelisted_quote_mints', 'g.whitelisted_quote_mints')
ST = ('let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:{unsafe{lts(32,skm.as_mut_ptr() as *mut u8)}/*shim: lifetime start of the sk slot between the fee_configurable load and the creator copy (creator stores ascending)*/;a.bonding_curve.creator},'
      'max_fee:unsafe{&*(ptp(24,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of max_fee*/.global.max_configurable_creator_fee_bps,'
      'mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled};')
WV = 'core::ptr::write_volatile(core::ptr::addr_of_mut!((*p).%s),%s);'
STV = ('let mut stu=core::mem::MaybeUninit::<CtoState>::uninit();let st=unsafe{let p=stu.as_mut_ptr();'
       'let (mf0,he0,fc0)=(g.max_configurable_creator_fee_bps,g.is_holder_reward_enabled,g.creator_fee_configurable);'
       + WV % ('cashback', 'cb0') + WV % ('holder_reward', 'hr0') + WV % ('mayhem', 'my0')
       + 'lts(32,skm.as_mut_ptr() as *mut u8);(*p).creator=a.bonding_curve.creator;'
       + WV % ('quote_locked', 'quote_locked') + WV % ('fee_configurable', 'fc0') + WV % ('holder_enabled', 'he0') + WV % ('max_fee', 'mf0')
       + 'stu.assume_init_ref()}/*shim: orig stxb order -0xe,-0xf,-0x10 | creator | -0xd,-0xb,-0xc | max_fee; lifetime start of the sk slot before the creator copy*/;')
def _valr(s):
    import re
    m = re.search(r'validate\(&st,hopt,fee,new,holder_key,sk', s)
    assert m
    return s.replace(m.group(0), 'validate(st,hopt,fee,new,holder_key,sk', 1)
G['VE'] = [E(QL, G2 + EF2 + QLG), E(ST, STV), _valr]

# ---- S3n (w16a08 per-arm holder flag), ported to main 53ec7fb53's validate text
SIG = 'holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);'
def _s3n(s):
    s = one(s, SIG, SIG.replace('sharing:&Pubkey)', 'sharing:&Pubkey,hf:&mut bool)'))
    s = one(s, '{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{', '{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*hf=true;*holder_key}else{')
    s = one(s, 'return Err(error!(PumpError::InvalidCreator));}t};', 'return Err(error!(PumpError::InvalidCreator));}*hf=false;t};')
    import re
    m = re.search(r'let mut target=validate\((&?)st,hopt,fee,new,holder_key,sk\)\?;', s)
    assert m
    s = s.replace(m.group(0), 'let mut hf=false;let mut target=validate(%sst,hopt,fee,new,holder_key,sk,&mut hf)?;' % m.group(1), 1)
    s = one(s, '(holder,cashback,target,sharing_update,collect_old,skip)}', '(hf,cashback,target,sharing_update,collect_old,skip)}')
    s = one(s, 'curve.is_holder_reward=holder.unwrap_or(false);', 'curve.is_holder_reward=_holder;')
    s = one(s, 'is_holder_reward:a.bonding_curve.is_holder_reward,', 'is_holder_reward:holder.unwrap_or(false),')
    return s
G['S3'] = [_s3n]

# ---- w17a16 outline core V = tf_g3 + 306 None 3:1 (cold Some arm, payload through a raw pointer) + crl3 + threaded head Dx49
ARM_V = "else{sharing_update=Some(args.0);target=unsafe{core::ptr::read_volatile(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer; passthrough on the accounts pointer it derefs*/.creator;(false,true)}}"
def _tfhead(s):
    a = "let (_holder,cashback,target,sharing_update,collect_old,skip)={ "
    return one(s, a, a + "let creator=a.bonding_curve.creator;")
TF = [_tfhead, E(ARM_V, "else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
SIGV = "fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey"
L306 = "  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
E306 = "return Err(error!(PumpError::CtoNewCreatorRequired))"
def _cfn(s):
    i = s.index(SIGV); j = s.index('{let holder=hopt==Some(true);', i) + len('{let holder=hopt==Some(true);')
    return s[:j] + "#[cold]fn cold(){}/*shim: empty #[cold] fn, fully inlined; marks a path cold for the inliner*/" + s[j:]
L306CP = ("  let t=if unsafe{expect_p(new.is_none(),true,%s)}/*shim: 306 None probability (llc weight)*/{" + E306 +
          ";}else{cold()/*shim: cold Some arm, 307/312 to_string outline*/;unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};")
CP75 = [_cfn, E(L306, L306CP % '0.75')]
CRL3 = [E('let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&', 'let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&')]
L289 = " if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
L296 = " if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}"
L298A = " let target=if holder{if unsafe{pt1(3,new.is_some())}"
def Dx(hold):
    return [E(L289, " let target=if if st.holder_reward{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}true}else if " + hold + "{"),
            E(L296, "  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}"),
            E(L298A, " {if unsafe{pt1(3,new.is_some())}")]
DX49 = Dx("unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/")
G['OL'] = TF + CP75 + CRL3 + DX49
G['OLb'] = TF + CP75          # outline only (no validate order, no crl3)

# ---- fo (w16a24): the validated fee as an out-param set only by the fee arm after the range check; 757 and pargs read it
R338 = 'if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}'
def _fo(s):
    import re
    if 'hf:&mut bool)->Result<Pubkey>' in s:
        s = one(s, 'hf:&mut bool)->Result<Pubkey>', 'hf:&mut bool,fo:&mut Option<u64>)->Result<Pubkey>')
    else:
        s = one(s, 'sharing:&Pubkey)->Result<Pubkey>', 'sharing:&Pubkey,fo:&mut Option<u64>)->Result<Pubkey>')
    s = one(s, R338, R338[:-len('}None=>{}}')] + '*fo=Some(f);}None=>{}}')
    s = one(s, 'let hopt=holder;', 'let hopt=holder;let mut fo:Option<u64>=None;')
    m = re.search(r'validate\((&?)st,hopt,fee,new,holder_key,sk(,&mut hf)?\)\?;', s)
    assert m
    s = s.replace(m.group(0), m.group(0)[:-3] + ',&mut fo)?;', 1)
    s = one(s, 'cashback,target,sharing_update,collect_old,skip)};', 'cashback,target,sharing_update,collect_old,skip,fo)};')
    s = one(s, 'let (_holder,cashback,target,sharing_update,collect_old,skip)={', 'let (_holder,cashback,target,sharing_update,collect_old,skip,fo)={')
    s = one(s, 'if let Some(f)=fee{curve.creator_fee_bps=f;}', 'if let Some(f)=fo{curve.creator_fee_bps=f;}')
    s = one(s, 'let pargs=(target,a.bonding_curve.is_holder_reward,fee);', 'let pargs=(target,a.bonding_curve.is_holder_reward,fo);')
    return s
G['FO'] = [_fo]
# FOp: fo plus one passthrough on its tag (w17a15 probe a1: the constant tag phi stays ONE phi for the 757 test and the pargs store)
G['FOp'] = [_fo, E('let mut target=target;', 'let mut target=target;let fo=unsafe{core::mem::transmute::<[u64;2],Option<u64>>({let w=core::mem::transmute::<Option<u64>,[u64;2]>(fo);[pt64(40,w[0]),w[1]]})}/*shim: passthrough on the validated-fee tag phi (one phi for the 757 test and the pool CPI tag)*/;')]

# ---- HL2: holder late in validate too (after the mayhem test, as the original's and-1 reload) + execute's holder/cashback after validate
def _vhl(s):
    s = one(s, '->Result<Pubkey>{let holder=hopt==Some(true);', '->Result<Pubkey>{')
    return one(s, 'if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}', 'if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}let holder=hopt==Some(true);')
G['HL2'] = [_hl, _vhl]
G['VHL'] = [_vhl]
