# w17a16 outlinerepay genes on main bf01b5fd9: exact single-occurrence (old,new) edits or callables on admin_cto.rs.
# Line count must not change. Every steering construct carries a same-line /*shim: ...*/ marker.
G = {}
SIG = "fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"
L306 = "  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
E306 = "return Err(error!(PumpError::CtoNewCreatorRequired))"
STH2 = "{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"
ARM_V0 = "else{sharing_update=Some(args.0);target=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;(false,true)}}"
ARM_V = "else{sharing_update=Some(args.0);target=unsafe{*(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: passthrough on the accounts pointer the curve box reload derefs*/.creator;(false,true)}}"
VCALL = "validate(&st,hopt,fee,new,holder_key,&sk)?"


def one(s, a, b):
    c = s.count(a)
    assert c == 1, (c, a[:120])
    return s.replace(a, b)


def E(a, b):
    return lambda s: one(s, a, b)


# C1: empty #[cold] fn at the head of the 306 Some arm (w14a07 c1 / w17a02 c306 / w16a22 C1)
C1 = [E(SIG, SIG + "#[cold]fn cold(){}/*shim: empty #[cold] fn, fully inlined; marks a path cold for the inliner*/"),
      E(L306, "  let t=if let Some(t)=new{cold()/*shim: cold Some arm, 307/312 to_string outline*/;t}else{" + E306 + ";};")]
# tf_g3 (w15a21 creator binding), replacing main's volatile curve reload in the shared non-holder arm
def _tfhead(s):
    a = "let (_holder,cashback,target,sharing_update,collect_old,skip)={ "
    assert s.count(a) == 1
    return s.replace(a, a + "let creator=a.bonding_curve.creator;")
def _tfhead2(s):
    a = "let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();let st=CtoState{"
    assert s.count(a) == 1
    return s.replace(a, "let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();let creator=a.bonding_curve.creator;let st=CtoState{")
TF = [_tfhead,
      E(ARM_V, "else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
TF2 = [_tfhead2,
      E(ARM_V, "else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
# tf_g3 variant that keeps main's volatile reload as the creator binding source
TFV = [E(STH2, "{ let creator=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;" + STH2[2:]),
       E(ARM_V, "else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
# P: 306 None probability via expect_p with the payload read through a raw pointer (w17a02 p306_*)
L306P = ("  let t=if unsafe{expect_p(new.is_none(),true,%s)}/*shim: 306 None probability*/{" + E306 +
         ";}else{unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};")


def P(p):
    return [E(L306, L306P % p)]


# tAn2 (w16a13): a temporary &Some(new) read only by validate's 306 double test
SIG_R = SIG.replace("new:Option<Pubkey>,", "new:Option<Pubkey>,su:&Option<Option<Pubkey>>,")
AN2 = [E(SIG, SIG_R),
       E(L306, "  let t=match (*su,new){(Some(Some(_)),Some(t))=>t,_=>" + E306 + "};"),
       E(VCALL, "validate(&st,hopt,fee,new,&Some(new),holder_key,&sk)?")]

G['m'] = []
G['c1'] = C1
G['tfc1'] = TF + C1
G['tfvc1'] = TFV + C1
G['tf'] = TF
G['tfp67'] = TF + P('0.6667')
G['p67'] = P('0.6667')
G['tan2'] = TF + AN2
G['an2'] = AN2

# C1 + P: 306 None probability with the cold() marker kept in the Some arm (payload through a raw pointer)
L306CP = ("  let t=if unsafe{expect_p(new.is_none(),true,%s)}/*shim: 306 None probability (llc weight)*/{" + E306 +
          ";}else{cold()/*shim: cold Some arm, 307/312 to_string outline*/;unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};")
CFN = E(SIG, SIG + "#[cold]fn cold(){}/*shim: empty #[cold] fn, fully inlined; marks a path cold for the inliner*/")
def CP(p):
    return [CFN, E(L306, L306CP % p)]
for nm, p in (('50','0.5'),('60','0.6'),('67','0.6667'),('75','0.75'),('80','0.8'),('90','0.9')):
    G['tfcp' + nm] = TF + CP(p)
# repay pieces
SHN = 'let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['crl3'] = [E('let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&', 'let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&')]
G['crl2'] = [E(SHN, 'let shared={let cr=a.bonding_curve.creator;let sk=a.sharing_config.key();cr==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
# g1 (w15a09/w15a13): creator from st before validate, target=creator in the shared arm (replaces main's volatile reload)
G['g1'] = [E('let sk=a.sharing_config.key();let mut target=validate(', 'let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate('),
           E(ARM_V, "else{sharing_update=Some(args.0);target=creator;(false,true)}}")]
G['g1c1'] = G['g1'] + C1
G['tfc1crl3'] = TF + C1 + G['crl3']
G['tfc1crl2'] = TF + C1 + G['crl2']

# ---- repay pieces priced on the source outline base B75 = tf_g3 + cold() + expect_p(new.is_none(),true,0.75) ----
B75 = TF + CP('0.75')
G['b75'] = B75
import re as _re
def _k8(s):
    i = s.index('let shared={let ')
    j = s.index('let mut hkx=', i)
    k = s.index('let quote_locked=', j)
    sh = s[i:j]; pda = s[j:k]
    return s[:i] + pda + sh + s[k:]
G['k8'] = [_k8]
_RV = 'read_volatile(holder_key as *const Pubkey as *const u8)'
def _b01(s):
    s = one(s, 'holder_key:&Pubkey,sharing:&Pubkey)', 'holder_key:Pubkey,sharing:&Pubkey)')
    s = one(s, 'holder_key,&sk)?', '*holder_key,&sk)?')
    s = one(s, '*holder_key}else{', 'holder_key}else{')
    s = one(s, '||t==*holder_key{', '||t==holder_key{')
    s = s.replace(_RV, 'read_volatile(&holder_key as *const Pubkey as *const u8)')
    return s
G['b01'] = [_b01]
G['Fa'] = [E('validate(&st,hopt,fee,new,', 'validate(&st,hopt,fee,args.0,')]
G['t1n'] = [E("if shared{if holder{sharing_update=Some(None);(false,false)}else{", "if shared{if new.is_none(){sharing_update=Some(None);(false,false)}else{")]

# ---- V-order: explicitly threaded validate head (the 'direct' rustc creation order: bb16 not glued to its successors) ----
L289 = " if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
L296 = " if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}"
L298 = " let target=if holder{if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
def D(hold, e289="!(hopt==Some(true))"):
    return [E(L289, " let target=if if st.holder_reward{if " + e289 + "{return Err(error!(PumpError::HolderRewardCreatorImmutable));}true}else if " + hold + "{"),
            E(L296, "  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}"),
            E(L298, " {if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
G['D'] = D("holder")
G['Dx49'] = D("unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/")
G['Dh'] = D("holder", "!holder")
G['Dhx49'] = D("unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/", "!holder")

# ---- repay knobs on the V-order outline base ----
def SHW(p):
    return [E("if shared{if holder{sharing_update=Some(None);(false,false)}else{", "if unsafe{expect_p(shared,true," + p + ")}/*shim: shared split weight (llc block placement)*/{if holder{sharing_update=Some(None);(false,false)}else{")]
G['shw625'] = SHW('0.625'); G['shw67'] = SHW('0.6667'); G['shw375'] = SHW('0.375')
G['tfp67'] = TF + P('0.6667')
G['tfp75'] = TF + P('0.75')
for nm, p in (('70','0.7'),('80','0.8'),('85','0.85')):
    G['b' + nm] = TF + CP(p)
G['Dx45'] = D("unsafe{expect_p(holder,true,0.45)}/*shim: !hr holder test 45:55 (MBP places the 306 test after the !hr holder test)*/")
G['Dx48'] = D("unsafe{expect_p(holder,true,0.48)}/*shim: !hr holder test 48:52 (MBP places the 306 test after the !hr holder test)*/")

# w17a06 byte-adding compare-in-memory shims (+32 B each on main)
G['hvw'] = [E("if a.holder_creator_vault.key()!=dest{", "if {let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.holder_creator_vault.key()==dest)};/*shim: holder-vault key compare kept in memory*/!c}{")]
G['pow'] = [E("let pool_updated=a.pool.owner==&AMM && ", "let pool_updated={let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.pool.owner==&AMM)};/*shim: pool owner compare kept in memory*/c} && ")]
G['V'] = TF + P('0.75') + G['crl3'] + G['Dx49']

L312P = "  if unsafe{expect_p(t==*sharing,true,0.625)}/*shim: 312 t==sharing memcmp equal-likely 20:12 (llc spill colour; was the libcall 12:20)*/||t==*holder_key{"
def P312(p):
    return [E(L312P, "  if unsafe{expect_p(t==*sharing,true," + p + ")}/*shim: 312 t==sharing memcmp weight (keeps the 312 to_string site warm at V)*/||t==*holder_key{")]
G['p312_90'] = P312('0.9'); G['p312_80'] = P312('0.8'); G['p312_97'] = P312('0.97')
G['W'] = G['V'] + G['shw625'] + G['hvw']

def CMP(old, expr, neg, what):
    return [E(old, "{let mut c=false;unsafe{core::ptr::write_volatile(&mut c," + expr + ")};/*shim: " + what + " compare kept in memory*/" + ("!c" if neg else "c") + "}")]
G['cdw'] = CMP("st.creator!=Pubkey::default()", "st.creator==Pubkey::default()", True, "creator==default")
G['sco'] = CMP("a.sharing_config.owner==&FEES", "a.sharing_config.owner==&FEES", False, "sharing_config owner")
G['wown'] = CMP("a.current_creator.owner!=&anchor_lang::system_program::ID", "a.current_creator.owner==&anchor_lang::system_program::ID", True, "current_creator owner")
G['qnat'] = CMP("q==anchor_spl::token::spl_token::native_mint::ID", "q==anchor_spl::token::spl_token::native_mint::ID", False, "quote==native")

G['cnat'] = CMP("let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID", False, "wallet quote==native")
G['cnat'][0] = E("let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "let collection_native={let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID)};/*shim: wallet quote==native compare kept in memory*/c};")
G['snat'] = [E("let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;", "let native={let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID)};/*shim: sweep quote==native compare kept in memory*/c};")]

# Ds: main's 289 statement kept first (constant-pool order: k_u32_83 before k_u32_89), then the threaded head re-tests hr
HW49 = "unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/"
G['Ds'] = [E(L289, L289 + "let target=if if st.holder_reward{true}else if " + HW49 + "{"),
           E(L296, "  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}"),
           E(L298, " {if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
G['Dh2'] = [E(L289, " let target=if if st.holder_reward{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}true}else if " + HW49 + "{"),
            E(L296, "  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}"),
            E(L298, " {if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
G['Vs'] = TF + P('0.75') + G['crl3'] + G['Ds']
G['X5s'] = G['Vs'] + G['shw625'] + G['hvw'] + G['cdw'] + G['cnat'] + G['wown']

# Dm: hr test as an integer match (MIR switchInt [1: hr path, otherwise: else chain]): RPO codegens the hr path (289) first
def DM(head):
    return [E(L289, " let target=if match " + head + "{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}true}_=>if " + HW49 + "{"),
            E(L296, "  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}"),
            E(L298, " {if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
G['Dm'] = DM("st.holder_reward as u8{1=>")
G['Dmb'] = DM("st.holder_reward{true=>")
G['Vm'] = TF + P('0.75') + G['crl3'] + G['Dm']
G['Vmb'] = TF + P('0.75') + G['crl3'] + G['Dmb']
G['X5m'] = G['Vm'] + G['shw625'] + G['hvw'] + G['cdw'] + G['cnat'] + G['wown']

def MEM(expr, what):
    return "{let mut c=false;unsafe{core::ptr::write_volatile(&mut c," + expr + ")};/*shim: " + what + " kept in memory*/c}"
G['f410'] = [E("require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);", "require!(" + MEM("a.bonding_curve.creator_fee==0", "410 creator_fee==0") + ",PumpError::CreatorFeesNotSwept);")]
G['f660'] = [E("require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);", "require!(" + MEM("token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0", "660 raw amount==0") + ",PumpError::CtoSharedVaultFrozen);")]
G['f719'] = [E("require!(amount==0,PumpError::CtoSharedVaultFrozen);", "require!(" + MEM("amount==0", "719 amount==0") + ",PumpError::CtoSharedVaultFrozen);")]
G['wexe'] = [E("if a.current_creator.executable{msg!(", "if " + MEM("a.current_creator.executable", "wallet executable flag") + "{msg!(")]
G['WmC'] = G['Vm'] + G['shw625'] + G['hvw'] + G['cdw']

G['noq'] = [E("(unsafe{expect(q==Pubkey::default(),false)})/*shim: default-quote test weighted 1:2000*/||", "q==Pubkey::default()||")]
G['nopt8'] = [E("if coin_present&((unsafe{pt8(6,*(&do_coin as *const bool as *const u8))}&1)!=0)/*shim: passthrough on the do_coin byte at the AMM collect test*/{", "if coin_present&do_coin{")]
G['nopt1'] = [E(" {if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{", " {if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]

G['p8'] = [E("// layout-pad(183): aligns the next Source site with the original line\n\n", "// layout-pad(183): aligns the next Source site with the original line\n#[repr(C,align(8))]struct P8(Pubkey);/*shim: 8-aligned validate return, target pieces on 8-byte boundaries*/\n"),
           E("->Result<Pubkey>{let holder=hopt==Some(true);", "->Result<P8>{let holder=hopt==Some(true);"),
           E("Ok(target)}pub fn execute", "Ok(P8(target))}pub fn execute"),
           E("let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;", "let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?.0;")]
G['Wm2'] = G['WmC'] + G['noq'] + G['nopt1']

def _x312h(s):
    a = "||t==*holder_key{"
    assert s.count(a) == 1
    return s.replace(a, "||unsafe{expect(t==*holder_key,false)}/*shim: 312 holder_key compare unlikely 1:2000 (llc placement)*/{")
G['x312h'] = [_x312h]
G['nolte'] = [E("{unsafe{lte(32,&t as *const Pubkey as *mut u8)}/*shim: lifetime end of t at the 312 InvalidCreator error (t is dead there; recolours that block's error temps)*/;return Err(error!(PumpError::InvalidCreator));}", "{return Err(error!(PumpError::InvalidCreator));}")]
G['Z1'] = G['Wm2'] + G['cnat'] + G['wown'] + G['wexe']

G['Z1xp'] = G['WmC'] + G['noq'] + G['cnat'] + G['wown'] + G['wexe'] + G['x312h']
G['Wx'] = G['Wm2'] + G['x312h']

G['WX'] = G['WmC'] + G['noq'] + G['x312h']

G['q'] = G['WX'] + G['cnat'] + G['wown']
def _swap_tf(genes):
    return [TF2[0] if g is TF[0] else g for g in genes]
G['q2'] = _swap_tf(G['q'])
G['Vm2'] = _swap_tf(G['Vm'])

G['tf3'] = [E("(creator stores ascending)*/;a.bonding_curve.creator},max_fee:", "(creator stores ascending)*/;creator},max_fee:")]
G['shw60'] = SHW('0.6'); G['shw70'] = SHW('0.7')
def _rep(genes, old, new):
    return [new[0] if g is old[0] else g for g in genes]
G['WX60'] = _rep(G['WX'], G['shw625'], G['shw60'])
G['WX70'] = _rep(G['WX'], G['shw625'], G['shw70'])

G['vsk'] = [E("let sk:&Pubkey=unsafe{skm.as_mut_ptr().write(a.sharing_config.key());&*skm.as_ptr()};", "let sk:&Pubkey=unsafe{skm.as_mut_ptr().write(core::ptr::read_volatile(&a.sharing_config)/*shim: volatile reload of the sharing_config account ref for the sk copy*/.key());&*skm.as_ptr()};")]

for _nm,_p in (('55','0.55'),('65','0.65'),('75','0.75'),('80','0.8'),('90','0.9')):
    G['shw'+_nm] = SHW(_p)
    G['WXv'+_nm] = _rep(G['WX'], G['shw625'], G['shw'+_nm]) + G['vsk']
G['WXv'] = G['WX'] + G['vsk']

G['ph334'] = [E(" unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;if st.mayhem{", " if st.mayhem{"),
              E("  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}", "  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}")]

def QV(call, what):
    return ("match " + call + "{Ok(v)=>v,Err(e)=>{let mut r=core::mem::MaybeUninit::<anchor_lang::error::Error>::uninit();unsafe{core::ptr::write_volatile(r.as_mut_ptr(),e)};/*shim: " + what + " ? residual kept in memory*/return Err(unsafe{r.assume_init()})}}")
G['qr560'] = [E("let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;", "let do_coin=coin_present&&!" + QV("token_frozen(a.coin_creator_vault_ata.as_ref())", "coin token_frozen") + ";")]
G['qr559'] = [E("&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);", "&&!" + QV("token_frozen(a.creator_vault_quote_token_account.as_ref())", "quote token_frozen") + ");")]
G['WXvp'] = G['WX'] + G['vsk'] + G['ph334']

G['qr649'] = [E("let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;", "let amm_frozen=amm_present&&" + QV("token_frozen(a.coin_creator_vault_ata.as_ref())", "sweep amm token_frozen") + ";")]
G['qrpbc'] = [E("crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;", QV("crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)", "prepare_bonding_curve") + ";")]


def apply(s, genes):
    n0 = s.count('\n')
    for g in genes:
        s = g(s)
    assert s.count('\n') == n0, 'line count changed'
    return s


if __name__ == '__main__':
    import sys
    path, names = sys.argv[1], sys.argv[2].split('+')
    s = open(path).read()
    genes = []
    for n in names:
        if n:
            genes += G[n]
    r = apply(s, genes)
    open(path, 'w').write(r)
