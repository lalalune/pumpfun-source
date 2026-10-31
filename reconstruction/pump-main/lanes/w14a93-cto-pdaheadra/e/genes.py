SH='a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
PDA='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
QL='let quote_locked={let q=a.bonding_curve.quote_mint;'
G={
'main':[],
'hL':[(SH,'a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
'pda':[('let shared='+SH+PDA, PDA+'let shared='+SH)],
'fl':[(QL,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QL),
      ('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin','mayhem:my0,holder_reward:hr0,cashback:cb0')],
'hkc':[('validate(&st,hopt,fee,new,&holder_key,&sk)','validate(&st,hopt,fee,new,&{holder_key},&sk)')],
}
SHL='a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
QLF='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
STF='let st=CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable};'
def st(order):
    f={'c':'creator:a.bonding_curve.creator','x':'max_fee:a.global.max_configurable_creator_fee_bps','m':'mayhem:a.bonding_curve.is_mayhem_mode','h':'holder_reward:a.bonding_curve.is_holder_reward','b':'cashback:a.bonding_curve.is_cashback_coin','q':'quote_locked','e':'holder_enabled:a.global.is_holder_reward_enabled','f':'fee_configurable:a.global.creator_fee_configurable'}
    return [(STF,'let st=CtoState{'+','.join(f[k] for k in order)+'};')]
G.update({
# holder arg vs computed bool in the shared arm
'hb':[('if shared{if holder{','if shared{if hopt==Some(true){')],
'hbm':[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=matches!(hopt,Some(true));')],
'hbu':[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=hopt.unwrap_or(false);')],
# mint key copy placement
'mkr':[('let mint=a.mint.key();','let mint=&a.mint.key();')],
'mki':[('let mint=a.mint.key();',''),('mint.as_ref()],&crate::ID);holder_key','a.mint.key().as_ref()],&crate::ID);holder_key')],
# hk binding
'hkd':[(PDA,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);let holder_key=hk.0;')],
'hkt':[(PDA,'let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')],
'hkl':[(PDA,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'),('let quote_locked={','holder_key=hk.0;let quote_locked={')],
# quote_locked position (pda-first base: PDA, shared, QL)
'qlA':[(QLF,''),('let holder_key;let hk=',QLF+'let holder_key;let hk=')],
'qlB':[(QLF,''),('holder_key=hk.0;let shared=','holder_key=hk.0;'+QLF+'let shared=')],
# shared spellings
'sif':[('let shared='+SHL,'let shared=if a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES{!a.sharing_config.data_is_empty()}else{false};')],
'smut':[('let shared='+SHL,'let mut shared=false;if a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES{shared=!a.sharing_config.data_is_empty();}')],
'sc':[('let shared='+SHL,'let sc=&a.sharing_config;let shared=a.bonding_curve.creator==sc.key()&&sc.owner==&FEES&&!sc.data_is_empty();')],
'sai':[('let shared='+SHL,'let sc=a.sharing_config.to_account_info();let shared=a.bonding_curve.creator==sc.key()&&sc.owner==&FEES&&!sc.data_is_empty();')],
'bc':[('let shared='+SHL,'let bc=&a.bonding_curve;let shared=bc.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')],
})
for o in ['xcmhbqef','cmhbqxef','chmbqxef','cbhmqxef','qcxmhbef','cxmhbqfe','cxefmhbq','mhbcxqef','cxhmbqef','cxbhmqef']:
    G['st_'+o]=st(o)
G['mkl']=[('let mint=a.mint.key();',''),('mint.as_ref()],&crate::ID);holder_key=hk.0;','a.mint.key().as_ref()],&crate::ID);holder_key=hk.0;let mint=a.mint.key();')]
G['n']=[]
import itertools as _it
_SEG={'S':'let shared='+SHL,'P':PDA,'Q':QLF,'F':'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'}
_HEAD='let shared='+SH+PDA+QLF
for _p in _it.permutations('SPQF'):
    _k=''.join(_p)
    G['o_'+_k]=[(_HEAD,''.join(_SEG[c] for c in _p)),('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin','mayhem:my0,holder_reward:hr0,cashback:cb0')]
for _p in _it.permutations('SPQ'):
    _k=''.join(_p)
    G['o_'+_k]=[(_HEAD,''.join(_SEG[c] for c in _p))]
