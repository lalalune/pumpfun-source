# w16a18 devoltie genes: exact (old,new) replacements on admin_cto.rs at main 599891304 (line count kept by scr.py).
# Imports w16a02's genes_fk library (k_req*, k_rkn307, ...) and adds the placeholder removals and fee-arm forms.
import genes_fk as _fk
G=dict(_fk.G); apply=None
def apply(s,names):
    for n in names:
        for e in G[n]:
            if callable(e): s=e(s); continue
            if len(e)==3: a,b,k=e
            else: (a,b),k=e,1
            c=s.count(a)
            if c!=k: raise Exception(f'gene {n}: {c} occurrences (want {k}) of {a[:120]!r}')
            s=s.replace(a,b)
    return s
V='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
# vb: drop the line-334 placeholder (pure fill, -8 B)
G['vb']=[('  '+V+'if !st.fee_configurable','  if !st.fee_configurable')]
# v338: drop the line-338 placeholder (range-check OK block anchor)
G['v338']=[('{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'+V+'}None=>{}}','{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}')]
# fee-arm forms (apply after vb; the 338 placeholder is kept unless v338)
_E338=V+'}None=>{}}'
G['nf']=[(' match fee{Some(f)=>{if st.quote_locked{',' match fee{None=>{}Some(f)=>{if st.quote_locked{'),(_E338,V+'}}')]
G['wc']=[(_E338,V+'}_=>{}}')]
G['ifl']=[(' match fee{Some(f)=>{if st.quote_locked{',' if let Some(f)=fee{if st.quote_locked{'),(_E338,V+'}')]
G['reff']=[(' match fee{Some(f)=>{if st.quote_locked{',' match &fee{Some(f)=>{let f=*f;if st.quote_locked{')]
# create_v2 / admin_cto_pool require! idioms for the whole fee arm (all four checks)
G['rq4']=G['k_req326']+G['k_req330']+[('if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','require!(st.fee_configurable,PumpError::CreatorFeeNotConfigurable);')]+G['k_req338']
G['rq338b']=[('if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}','require!(f!=0&&f<=st.max_fee,PumpError::CreatorFeeBpsOutOfRange);')]
G['rq338c']=[('if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}','require!((1..=st.max_fee).contains(&f),PumpError::CreatorFeeBpsOutOfRange);')]
# validate head: require! for 284/289/298 and the create_v2 require_keys_neq! at 307
G['rqhead']=G['k_req284']+G['k_req289']+G['k_req298']
# ---- faithful fee-tag data flow (owner rule: fill must follow the original's data flow) ----
# fh: the fee arm becomes its own helper at the same lines (326-338) that RE-MAKES the fee (Ok(Some(f)) / Ok(None)), and
# execute uses the validated fee for the line-757 curve store and the admin_cto_pool tag, so the fee argument dies after
# the checks and the tag becomes a phi of constants (the original's mov64 r7,1 in the range-check OK block, mov64 r7,0 on
# the None paths). validate keeps Result<Pubkey>. No placeholder left.
_FA=('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};\n// layout-pad(13): aligns the next Source site with the original line\n let cashback=if holder{false}else{st.cashback};\n\n\n\n\n\n\n\n\n\n\n\n match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}\n// layout-pad(3): aligns the next Source site with the original line\n\n\n  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}\n\n\n\n  '+V+'if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}\n\n\n\n  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'+V+'}None=>{}}\n Ok(target)}pub fn execute(')
def _fh(sig_fee,body338,call):
    new=('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};\n// layout-pad(13): aligns the next Source site with the original line\n Ok(target)}\n\n\n\n\n\n\n\n\n\n\n\n'
         'fn fee_checked(st:&CtoState,cashback:bool,fee:Option<u64>)->Result<Option<u64>>{match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}\n// layout-pad(3): aligns the next Source site with the original line\n\n\n  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}\n\n\n\n  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}\n\n\n\n  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'+body338+'\npub fn execute(')
    return [(_FA,new),('fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,','fn validate(st:&CtoState,hopt:Option<bool>,new:Option<Pubkey>,'),
            ('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let mut target=validate(&st,hopt,new,&holder_key,&sk)?;'+call),
            ('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fee)={'),
            ('(holder,cashback,target,sharing_update,collect_old,skip)}','(holder,cashback,target,sharing_update,collect_old,skip,fee)}')]
G['fh']=_fh(None,'Ok(Some(f))}None=>Ok(None)}}','let fee=fee_checked(&st,cashback,fee)?;')
# fh_mt: same helper, match-expression form returning the re-made Option at the end
G['fh_mt']=_fh(None,'}None=>{}}Ok(fee)}','let fee=fee_checked(&st,cashback,fee)?;')
# fh757 / fhcpi: the re-made fee (vfee) feeds only the line-757 curve store / only the admin_cto_pool tag
def _fhv(use757,usecpi):
    g=_fh(None,'Ok(Some(f))}None=>Ok(None)}}','let vfee=fee_checked(&st,cashback,fee)?;')
    g=[(a,b.replace('skip,fee)','skip,vfee)')) for a,b in g]
    if use757: g.append(('if let Some(f)=fee{curve.creator_fee_bps=f;}','if let Some(f)=vfee{curve.creator_fee_bps=f;}'))
    if usecpi: g.append(('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,vfee);'))
    return g
G['fh757']=_fhv(True,False)
G['fhcpi']=_fhv(False,True)
# _i: the same fee helper marked #[inline] (MIR-inlined, so LLVM's inliner sees main's call graph: f_fh un-inlines sweep)
def _inl(g): return [(a,b.replace('\nfn fee_checked(','\n#[inline] fn fee_checked(')) for a,b in g]
G['fh_i']=_inl(G['fh']); G['fh757_i']=_inl(G['fh757']); G['fhcpi_i']=_inl(G['fhcpi']); G['fhmt_i']=_inl(G['fh_mt'])
# fh_and: one combined Result and one ? in execute (validate(..).and_then(fee helper)), to test the sweep cold-site cliff
_g=_fh(None,'Ok(Some(f))}None=>Ok(None)}}','')
G['fh_and']=[(a,b) for a,b in _g if not a.startswith('let mut target=validate(')]+[('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fee)=validate(&st,hopt,new,&holder_key,&sk).and_then(|t|Ok((t,fee_checked(&st,cashback,fee)?)))?;')]
