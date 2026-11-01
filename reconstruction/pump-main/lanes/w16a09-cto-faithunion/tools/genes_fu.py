# w16a09 faithunion genes: union classes of w15a11's validate/head cause table, written so that they compose.
# Experiment only. Each gene is a list of exact single-occurrence (old,new) replacements or callables s->s;
# the newline count must hold. Inherits the whole swarm library through genes_lac.
import os,sys,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_lac as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)

def _one(s,a,b):
    c=s.count(a); assert c==1,(c,a[:100]); return s.replace(a,b)
def _rx1(pat,rep):
    def f(s):
        n=len(re.findall(pat,s)); assert n==1,(n,pat); return re.sub(pat,rep,s)
    return f

E289="{return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
# ---- C/D: T289n (w15a25): 289 on `holder` itself, nested -> V-time threading, 307/312 outlined (orig pattern)
G['p289n']=[(" if st.holder_reward&&!(hopt==Some(true))"+E289," if st.holder_reward{if !holder"+E289+"}")]
G['p289e']=[(" if st.holder_reward&&!(hopt==Some(true))"+E289," if st.holder_reward&&holder==false"+E289)]
G['p289h']=[(" if st.holder_reward&&!(hopt==Some(true))"+E289," if st.holder_reward&&!holder"+E289)]
# ---- H: and-1 holder (w15a11 v14 = vmt; w15a25 U4 adds emt)
G['vmt']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=matches!(hopt,Some(true));')]
G['vuo']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=hopt.unwrap_or(false);')]
G['emt']=[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=matches!(hopt,Some(true));')]
G['euo']=[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=hopt.unwrap_or(false);')]
# ---- b01 / v01 (w15a11): validate takes holder_key by value (orig validate-entry key copy); 312 holder-first
_RVm='read_volatile(holder_key as *const Pubkey as *const u8)'
def _b01(s):
    s=_one(s,'holder_key:&Pubkey,sharing:&Pubkey)','holder_key:Pubkey,sharing:&Pubkey)')
    s=_one(s,'&holder_key,&sk)','holder_key,&sk)')
    s=_one(s,'*holder_key}else{','holder_key}else{')
    s=_one(s,'t==*holder_key','t==holder_key')
    if _RVm in s: s=s.replace(_RVm,'read_volatile(&holder_key as *const Pubkey as *const u8)')
    return s
G['b01']=[_b01]
def _v01(s):
    if 'if t==*sharing||t==holder_key{' in s: return _one(s,'if t==*sharing||t==holder_key{','if t==holder_key||t==*sharing{')
    return _one(s,'if t==*sharing||t==*holder_key{','if t==*holder_key||t==*sharing{')
G['v01']=[_v01]
# ---- E: entry copy of `new` survives only when validate reads the args copy (w15a10 Fa)
G['Fa']=[_rx1(r'validate\((&(?:mut )?st),hopt,fee,new,',r'validate(\1,hopt,fee,args.0,')]
# w15a10 qli: quote_locked inline in the CtoState literal (w13a41 t22)
# ---- F: per-arm phi constant (w15a20 ov1a): validate takes `shared`, non-holder arm yields st.creator when shared
def _ov1a(s):
    s=_one(s,'sharing:&Pubkey)->Result<Pubkey>','sharing:&Pubkey,shared:bool)->Result<Pubkey>')
    s=_one(s,'{return Err(error!(PumpError::InvalidCreator));}t};','{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};')
    n=len(re.findall(r'validate\(([^;]*?),&sk\)\?',s)); assert n==1
    s=re.sub(r'validate\(([^;]*?),&sk\)\?',r'validate(\1,&sk,shared)?',s)
    return s
G['ov1a']=[_ov1a]
# ---- G: CtoState literal order by field names (callable; composes with GPF's field-level edits)
def _ord(names):
    def f(s):
        m=re.search(r'let (mut )?st=CtoState\{([^}]*)\}',s); assert m
        fs=m.group(2).split(','); d={x.split(':')[0]:x for x in fs}; assert set(d)==set(names),(sorted(d),names)
        return s[:m.start(2)]+','.join(d[n] for n in names)+s[m.end(2):]
    return [f]
_F0=['fee_configurable','creator','max_fee','mayhem','holder_reward','cashback','quote_locked','holder_enabled']
G['G51']=_ord(['fee_configurable','cashback','creator','max_fee','mayhem','holder_reward','quote_locked','holder_enabled'])  # = mv_5_1
G['Gorig']=_ord(['cashback','holder_reward','mayhem','creator','quote_locked','fee_configurable','holder_enabled','max_fee'])
G['Gfc']=_ord(['fee_configurable','cashback','holder_reward','mayhem','creator','quote_locked','holder_enabled','max_fee'])
# ---- A/B: GPF (w15a28): PDA first (A) + `g` binding + curve bools first (B), field-level so it composes with G
_SH='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
_PDA='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
_QL='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)}'
_QLg='let g:&Global=&a.global;let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||g.whitelisted_quote_mints.contains(&q)}'
_QLf='let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+_QL
def _bools(s):
    s=_one(s,'mayhem:a.bonding_curve.is_mayhem_mode','mayhem:my0')
    s=_one(s,',holder_reward:a.bonding_curve.is_holder_reward',',holder_reward:hr0') if ',holder_reward:a.bonding_curve.is_holder_reward' in s else _one(s,'{holder_reward:a.bonding_curve.is_holder_reward','{holder_reward:hr0')
    s=_one(s,'cashback:a.bonding_curve.is_cashback_coin,','cashback:cb0,') if 'cashback:a.bonding_curve.is_cashback_coin,' in s else _one(s,'cashback:a.bonding_curve.is_cashback_coin}','cashback:cb0}')
    return s
def _gfields(s):
    s=_one(s,'fee_configurable:a.global.creator_fee_configurable','fee_configurable:g.creator_fee_configurable')
    s=_one(s,'max_fee:a.global.max_configurable_creator_fee_bps','max_fee:g.max_configurable_creator_fee_bps')
    s=_one(s,'holder_enabled:a.global.is_holder_reward_enabled','holder_enabled:g.is_holder_reward_enabled')
    return s
G['PDA']=[(_SH+_PDA,_PDA+_SH)]
G['F0']=[(_QL,_QLf),_bools]
G['GPF']=[(_SH+_PDA,_PDA+_SH),(_QL,_QLg),_bools,_gfields]
G['GF']=[(_QL,_QLg),_bools,_gfields]
# ---- w15a10 faithful entry forms, composable: V2 (sharing key by value too), qli (quote_locked inline), hkt (plain PDA)
def _v2(s):
    s=_b01(s) if 'holder_key:&Pubkey,' in s else s
    s=re.sub(r'sharing:&Pubkey(\)|,shared)',r'sharing:Pubkey\1',s,count=1)
    n=len(re.findall(r'holder_key,&sk\)|holder_key,&sk,',s)); assert n==1,n
    s=s.replace('holder_key,&sk)','holder_key,sk)').replace('holder_key,&sk,','holder_key,sk,')
    s=_one(s,'t==*sharing','t==sharing')
    return s
G['V2']=[_v2]
def _qli(s):
    m=re.search(r'let quote_locked=(\{let q=a\.bonding_curve\.quote_mint;[^}]*\});',s); assert m
    blk=m.group(1); s=s[:m.start()]+s[m.end():]
    m2=re.search(r'([,{])quote_locked([,}])',s); assert m2
    return s[:m2.start()]+m2.group(1)+'quote_locked:'+blk+m2.group(2)+s[m2.end():]
G['qli']=[_qli]
G['hkt']=[(_PDA,'let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')]
def _ov1a2(s):
    s=re.sub(r'(sharing:&?Pubkey)\)->Result<Pubkey>',r'\1,shared:bool)->Result<Pubkey>',s,count=1)
    s=_one(s,'{return Err(error!(PumpError::InvalidCreator));}t};','{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};')
    n=len(re.findall(r'validate\(([^;]*?),&?sk\)\?',s)); assert n==1
    s=re.sub(r'validate\(([^;]*?),(&?sk)\)\?',r'validate(\1,\2,shared)?',s)
    return s
G['ov1a']=[_ov1a2]
G['v01']=[_rx1(r'if t==(\*?sharing)\|\|t==(\*?holder_key)\{',r'if t==\2||t==\1{')]
