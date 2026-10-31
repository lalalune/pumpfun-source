# genes_w16.py: source genes of w15a29-cto-devolrepay as exact (old, new) replacements on admin_cto.rs at main 9120883.
# apply(text, ['devol','rep338']) gives devol-rep338.patch. Experiment only.
G={}
G['devol']=[('fn validate(st:&CtoState,','fn validate(st:&mut CtoState,'),
 (' if st.holder_reward&&!(hopt==Some(true)){',' let hr=st.holder_reward;if hr&&!(hopt==Some(true)){'),
 (' if holder&&!st.holder_reward&&!st.holder_enabled{',' if holder&&!hr&&!st.holder_enabled{'),
 ('{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}','{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable=false;}'),
 (' let st=CtoState{',' let mut st=CtoState{'),('validate(&st,','validate(&mut st,'),
 ('unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{','if !st.fee_configurable{')]
G['devol_nohr']=[e for e in G['devol'] if 'hr' not in e[1]]
_RG='if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable=false;}None=>{}}'
G['d_maxf']=[('st.fee_configurable=false;}None=>{}}','st.max_fee=f;}None=>{}}')]
G['rep338']=[(_RG,'let max=core::mem::replace(&mut st.max_fee,f);if f==0||f>max{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable=false;}None=>{}}')]
G['mx338']=[(_RG,'let max=st.max_fee;st.max_fee=f;if f==0||f>max{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable=false;}None=>{}}')]
G['rep338q']=[(_RG,'let max=core::mem::replace(&mut st.max_fee,f);if f==0||f>max{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.quote_locked=true;}None=>{}}')]
def apply(s,names):
    for n in names:
        for o,w in G[n]:
            assert s.count(o)==1,(n,o[:80]); s=s.replace(o,w)
    return s
