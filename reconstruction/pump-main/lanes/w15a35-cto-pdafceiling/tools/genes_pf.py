# w15a35 pdafceiling genes: w15a16 genes_mp library + PDA-first head orders re-anchored on main 9120883 (cs_blk shared,
# CtoState fee_configurable first). S = main's shared, L = creator-left shared (w14a09/w14a93 hL), P = holder_key PDA,
# Q = quote_locked, F = curve bool locals read right after the head (w14a93 fl).
import os,sys,itertools as _it
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_mp as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
SHN='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
SHL='let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
QLF='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
FL='let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'
STB='mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin'
HEAD=SHN+HK+QLF
SEG={'S':SHN,'L':SHL,'P':HK,'Q':QLF,'F':FL}
def _ord(o):
    e=[(HEAD,''.join(SEG[c] for c in o))]
    if 'F' in o: e.append((STB,'mayhem:my0,holder_reward:hr0,cashback:cb0'))
    return e
for _n in (3,4):
    for _p in _it.permutations('SPQF'[:_n]):
        G['o_'+''.join(_p)]=_ord(''.join(_p))
        if 'S' in _p: G['o_'+''.join(_p).replace('S','L')]=_ord(''.join(_p).replace('S','L'))
