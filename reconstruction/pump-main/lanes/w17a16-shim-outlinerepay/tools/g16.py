# w17a16 outlinerepay genes on main bf01b5fd9: exact single-occurrence (old,new) edits or callables on admin_cto.rs.
# Line count must not change. Every steering construct carries a same-line /*shim: ...*/ marker.
G = {}
SIG = "fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"
L306 = "  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
E306 = "return Err(error!(PumpError::CtoNewCreatorRequired))"
STH2 = "{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"
ARM_V0 = "else{sharing_update=Some(args.0);target=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;(false,true)}}"
ARM_V = "else{sharing_update=Some(args.0);target=unsafe{core::ptr::read_volatile(&(*(ptp(1,&**a as *const AdminCto as *const u8) as *const AdminCto)).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer; passthrough on the accounts pointer it derefs*/.creator;(false,true)}}"
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
TF = [E(STH2, "{ let creator=a.bonding_curve.creator;" + STH2[2:]),
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
G['crl3'] = [E(SHN, 'let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
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
