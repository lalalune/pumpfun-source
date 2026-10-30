# stitch10 gene library on main 7e6aa9c (admin_cto.rs). Each gene: list of (old,new) exact replacements, or callables s->s.
import re
F={'K':'key','L':'lamports','D':'data','O':'owner','R':'rent_epoch','S':'is_signer','W':'is_writable','E':'executable'}
def fexpr(p,c): f=F[c]; return f"{f}:{p}.{f}.clone()" if c in 'LD' else f"{f}:{p}.{f}"
ACC={ # name: (prefix up to literal, path, account expr for to_account_info)
 'pa':("pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();",'x','a.pool_authority'),
 'gl':("global:{let x:&AccountInfo= a.global.as_ref().as_ref();",'x','a.global'),
 'mi':("mint:{let x:&AccountInfo= a.mint.as_ref();",'x','a.mint'),
 'ea':("event_authority:",'a.pump_fees_event_authority','a.pump_fees_event_authority'),
 'tv':("pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();",'x','a.creator_vault_quote_token_account'),
}
def _find(s,acc):
    pre,p,e=ACC[acc]
    if acc=='ea':
        i=s.index("event_authority:AccountInfo{lamports:a.pump_fees_event_authority"); j=i+len(pre); k=s.index('}',j)+1
        return i,j,k,k  # whole = s[i:k]
    i=s.index(pre); assert s.count(pre)==1; j=i+len(pre); k=s.index('}',j)+1; assert s[k]=='}'; return i,j,k,k+1
def order(s,acc):
    i,j,k,end=_find(s,acc); lit=s[j:k]; fs=re.findall(r'(\w+):',lit[len('AccountInfo{'):-1])
    inv={v:c for c,v in F.items()}; return ''.join(inv[f] for f in fs)
def ordg(acc,letters):
    def g(s):
        i,j,k,end=_find(s,acc); p=ACC[acc][1]
        return s[:j]+'AccountInfo{'+','.join(fexpr(p,c) for c in letters)+'}'+s[k:]
    return [g]
def taig(acc):
    def g(s):
        i,j,k,end=_find(s,acc); name=s[i:s.index(':',i)]
        return s[:i]+f"{name}:{ACC[acc][2]}.to_account_info()"+s[end:]
    return [g]
G={}
for a in ACC: G['tai_'+a]=taig(a)
PU="let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"
G['pu_amm_keyfn']=[(PU,"let pool_updated=!a.pool.data_is_empty() && *a.pool.owner==a.pump_amm.key();")]
G['pu_amm_key']=[(PU,"let pool_updated=!a.pool.data_is_empty() && a.pool.owner==a.pump_amm.key;")]
EVA="authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),"
G['ev_mint_key']=[(EVA,"authority:a.admin_set_creator_authority.key(),mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),")]
G['ev_auth_deref']=[(EVA,"authority:*a.admin_set_creator_authority.key,mint,bonding_curve:a.bonding_curve.key(),")]
G['ev_cb_local']=[("is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:cashback,")]
G['ev_nc_target']=[("new_creator:a.bonding_curve.creator,","new_creator:target,")]
G['ev_hr_local']=[("is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback","is_holder_reward:holder,is_cashback")]
G['ev_nf_inline']=[("new_creator_fee_bps:nf,","new_creator_fee_bps:a.bonding_curve.creator_fee_bps,")]
G['ev_nf_unwrap']=[("new_creator_fee_bps:nf,","new_creator_fee_bps:fee.unwrap_or(old_fee),")]
EVT="let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,"
G['ev_ts_clockvar']=[(EVT,"let clock=Clock::get()?;let e=AdminCtoEvent{timestamp:clock.unix_timestamp,")]
G['ev_ts_map']=[(EVT,"let e=AdminCtoEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,")]
G['ev_ts_prepool']=[(EVT,"let e=AdminCtoEvent{timestamp:ts,"),(PU,"let ts=Clock::get()?.unix_timestamp;"+PU)]
PA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
G['pargs_hr_local']=[(PA,"let pargs=(target,holder,fee);")]
G['pargs_tgt_curve']=[(PA,"let pargs=(a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee);")]
CU="curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);"
G['cu_iflet']=[(CU,"if let Some(f)=fee{curve.creator_fee_bps=f;}")]
G['cu_oldunwrap']=[(CU,"curve.creator_fee_bps=fee.unwrap_or(old_fee);")]
G['nf_old']=[("let nf=a.bonding_curve.creator_fee_bps;","let nf=fee.unwrap_or(old_fee);")]
# ea back to the pre-#3267 x-binding form (same order)
G['ea_xbind']=[("event_authority:AccountInfo{lamports:a.pump_fees_event_authority.lamports.clone(),data:a.pump_fees_event_authority.data.clone(),key:a.pump_fees_event_authority.key,owner:a.pump_fees_event_authority.owner,rent_epoch:a.pump_fees_event_authority.rent_epoch,is_signer:a.pump_fees_event_authority.is_signer,is_writable:a.pump_fees_event_authority.is_writable,executable:a.pump_fees_event_authority.executable}","event_authority:{let x=&*a.pump_fees_event_authority;AccountInfo{lamports:x.lamports.clone(),data:x.data.clone(),key:x.key,owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}")]
def gene(name):
    if name in G: return G[name]
    m=re.fullmatch(r'o_(\w\w)_([KLDORSWE]{8})',name)
    if m: assert sorted(m.group(2))==sorted('KLDORSWE'); return ordg(m.group(1),m.group(2))
    if name.startswith('x47_'):
        import sys as _s,os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..','ext')); import genes47
        return genes47.G[name[4:]]
    m=re.fullmatch(r'lfx_([a-z]+)_(\w+?)(__(dl|aa|dlaa))?',name)
    if m: return lfx(m.group(1),m.group(2),m.group(4) or '')
    raise KeyError(name)
def apply(s,names):
    n0=s.count('\n')
    for nm in names:
        for e in gene(nm):
            if callable(e): s=e(s); continue
            a,b=e; c=s.count(a); assert c==1,(nm,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,'newline count changed'
    return s
# AdminCtoEvent literal evaluation order (parsed from the current source)
def _evget(s):
    i=s.index('let e=AdminCtoEvent{'); j=s.index('};',i); body=s[i+len('let e=AdminCtoEvent{'):j]
    fs=[]
    for f in body.split(','):
        n,_,v=f.partition(':'); fs.append((n,v if v else None))
    return i,j+2,fs
def _evlit(fs): return 'let e=AdminCtoEvent{'+','.join(n if v is None else f'{n}:{v}' for n,v in fs)+'};'
def evo(names,last=False):
    def g(s):
        i,j,fs=_evget(s); d=dict(fs); rest=[(n,v) for n,v in fs if n not in names]; mv=[(n,d[n]) for n in names]
        return s[:i]+_evlit(rest+mv if last else mv+rest)+s[j:]
    return [g]
def evswap(a,b):
    def g(s):
        i,j,fs=_evget(s); n=[x for x,_ in fs]; ia,ib=n.index(a),n.index(b); fs[ia],fs[ib]=fs[ib],fs[ia]
        return s[:i]+_evlit(fs)+s[j:]
    return [g]
G['evo_ts_last']=evo(['timestamp'],True)
G['evo_ts_after_bc']=evo(['authority','mint','bonding_curve','timestamp'])
G['evo_bc_first']=evo(['bonding_curve'])
G['evo_mint_first']=evo(['mint'])
G['evo_curve_first']=evo(['new_creator','is_holder_reward','is_cashback_coin'])
G['evo_curve_ts']=evo(['new_creator','is_holder_reward','is_cashback_coin','timestamp'])
G['evo_old_first']=evo(['old_creator','old_creator_fee_bps'])
G['evo_auth_last']=evo(['authority'],True)
G['evo_bc_last']=evo(['bonding_curve'],True)
G['evo_nc_last']=evo(['new_creator'],True)
G['evo_cb_last']=evo(['is_cashback_coin'],True)
G['evo_flags_first']=evo(['sharing_config_reset','swept_to_holder_vault','pool_updated'])
G['evo_hrcb_swap']=evswap('is_holder_reward','is_cashback_coin')
G['evo_auth_bc_swap']=evswap('authority','bonding_curve')
G['evo_auth_mint_swap']=evswap('authority','mint')
G['evo_ts_auth_swap']=evswap('timestamp','authority')
G['evo_nc_hr_swap']=evswap('new_creator','is_holder_reward')
# reverse knobs on f100a59
G['ev_hr_curve']=[("is_holder_reward:holder,is_cashback","is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback")]
G['cu_unwrapcur']=[("if let Some(f)=fee{curve.creator_fee_bps=f;}","curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);")]
G['cu_iflet_old']=[("if let Some(f)=fee{curve.creator_fee_bps=f;}","curve.creator_fee_bps=fee.unwrap_or(old_fee);")]
G['cu_match']=[("if let Some(f)=fee{curve.creator_fee_bps=f;}","match fee{Some(f)=>curve.creator_fee_bps=f,None=>{}}")]
G['cu_fee_first']=[("curve.creator=target;\n","if let Some(f)=fee{curve.creator_fee_bps=f;}curve.creator=target;\n"),("\n  if let Some(f)=fee{curve.creator_fee_bps=f;}\n","\n  \n")]
def gene(name):
    if name in G: return G[name]
    m=re.fullmatch(r'o_(\w\w)_([KLDORSWE]{8})',name)
    if m: assert sorted(m.group(2))==sorted('KLDORSWE'); return ordg(m.group(1),m.group(2))
    if name.startswith('x47_'):
        import sys as _s,os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..','ext')); import genes47
        return genes47.G[name[4:]]
    m=re.fullmatch(r'lfx_([a-z]+)_(\w+?)(__(dl|aa|dlaa))?',name)
    if m: return lfx(m.group(1),m.group(2),m.group(4) or '')
    raise KeyError(name)
def apply(s,names):
    n0=s.count('\n')
    for nm in names:
        for e in gene(nm):
            if callable(e): s=e(s); continue
            a,b=e; c=s.count(a); assert c==1,(nm,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,'newline count changed'
    return s
# #3277 (w14a24-cto-shareauth, kutluhaneth46): sharing CPI authority as an explicit clone with Rc locals first
G['sh_auth']=[("authority:a.admin_set_creator_authority.to_account_info(),global:","authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();let lamports=x.lamports.clone();let data=x.data.clone();AccountInfo{rent_epoch:x.rent_epoch,owner:x.owner,lamports:lamports,key:x.key,is_writable:x.is_writable,is_signer:x.is_signer,executable:x.executable,data:data}},global:")]
# ---- Rc-locals-first clone class (from #3277) over the sharing CPI accounts ----
SHL=['pool_authority','authority','global','mint','sharing_config','event_authority','program']
SHX={'pool_authority':'a.pool_authority.as_ref()','authority':'a.admin_set_creator_authority.as_ref()','global':'a.global.as_ref().as_ref()','mint':'a.mint.as_ref()','sharing_config':'a.sharing_config.as_ref()','event_authority':'&*a.pump_fees_event_authority','program':'a.pump_fees.as_ref()'}
def _shsplit(s):
    i=s.index('crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{')+len('crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{')
    j=s.index('},signer_seeds),val)?;',i)
    body=s[i:j]; parts={}; pos=[]
    for k,l in enumerate(SHL):
        p=0 if k==0 else body.index(','+l+':',pos[-1][1])+1; pos.append((l,p))
    for k,(l,p) in enumerate(pos):
        e=pos[k+1][1]-1 if k+1<len(pos) else len(body)
        parts[l]=body[p+len(l)+1:e]
    return i,j,parts
def _shjoin(s,i,j,parts): return s[:i]+','.join(f'{l}:{parts[l]}' for l in SHL)+s[j:]
def lit_order(init):
    m=re.search(r'AccountInfo\{(.*)\}',init); fs=re.findall(r'(\w+):',m.group(1)) if m else []
    inv={v:c for c,v in F.items()}; o=''.join(inv[f] for f in fs if f in inv)
    return o if len(o)==8 else None
def lf_text(expr,order,dfirst=False):
    loc='let data=x.data.clone();let lamports=x.lamports.clone();' if dfirst else 'let lamports=x.lamports.clone();let data=x.data.clone();'
    fx=lambda c:{'L':'lamports:lamports','D':'data:data'}.get(c,f'{F[c]}:x.{F[c]}')
    return '{let x:&AccountInfo='+expr+';'+loc+'AccountInfo{'+','.join(fx(c) for c in order)+'}}'
def lfg(label,order=None,dfirst=False):
    def g(s):
        i,j,parts=_shsplit(s); o=order or lit_order(parts[label]) or 'ROLKWSED'
        parts[label]=lf_text(SHX[label],o,dfirst); return _shjoin(s,i,j,parts)
    return [g]
LAB={'pa':'pool_authority','au':'authority','gl':'global','mi':'mint','sc':'sharing_config','ea':'event_authority','pr':'program'}
for k,l in LAB.items():
    G[f'lf_{k}']=lfg(l); G[f'lf_{k}_R']=lfg(l,'ROLKWSED'); G[f'lf_{k}_dl']=lfg(l,None,True)
CPP="admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),"
G['lf_cp']=[(CPP,"admin_cto_sharing_config(CpiContext::new_with_signer("+lf_text('a.pump_fees.as_ref()','ROLKWSED')+",")]
def lfo(k,order): return lfg(LAB[k],order)
for _o in ['ORLKWSED','RLOKWSED','ROKLWSED','ROLWKSED','ROLKSWED','ROLKWESD','ROLKWSDE','LDROKWSE','KLDORSWE','LKDORSWE','ROKWSELD']:
    G[f'lfau_{_o}']=lfo('au',_o)
# Rc-locals-first on to_account_info() fields of other CPIs: lfx_<site>_<label>[_dl|_aa]
SITES={'tcf':'crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{','cre':'anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account','ccf':'crate::pump_amm::cpi::accounts::CollectCoinCreatorFee{','pool':'crate::pump_amm::cpi::accounts::AdminCtoPool{','hcre':'anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account'}
def lfx(site,label,mode=''):
    def g(s):
        i=s.index(SITES[site]); assert s.count(SITES[site])==1
        m=re.compile(r'([,{])'+label+r':a\.(\w+)\.to_account_info\(\)').search(s,i)
        assert m and m.start()<s.index('}',i)+1+0 or True
        acct=m.group(2); expr=f'a.{acct}.as_ref()'+('.as_ref()' if 'aa' in mode else '')
        return s[:m.start()+1]+label+':'+lf_text(expr,'ROLKWSED','dl' in mode)+s[m.end():]
    return [g]
# curve-store order and tail statement order (65df90f)
CS=['  curve.creator=target;\n','  curve.is_cashback_coin=cashback;\n','  curve.is_holder_reward=holder;\n','  if let Some(f)=fee{curve.creator_fee_bps=f;}\n','  curve.can_edit_creator_fee=false;\n']
def csperm(order):
    return [(''.join(CS),''.join(CS[k] for k in order))]
for _i in range(4):
    _o=list(range(5)); _o[_i],_o[_i+1]=_o[_i+1],_o[_i]; G[f'cs_swap{_i}']=csperm(_o)
G['cs_canedit_first']=csperm([4,0,1,2,3])
G['cs_creator_last']=csperm([1,2,3,4,0])
G['cs_rev']=csperm([4,3,2,1,0])
G['cs_old_fee_first']=[("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;","let old_fee=curve.creator_fee_bps;let old_creator=curve.creator;")]
TN="let nf=a.bonding_curve.creator_fee_bps;"; TP="let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"; TA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
_T={'N':TN,'P':TP,'A':TA}
for _o in ['NAP','PNA','PAN','ANP','APN']:
    G['tl_'+_o]=[(TN+TP+TA,''.join(_T[c] for c in _o))]
G['tl_nf_late']=[(TN+TP+TA,TP+TA),(" let e=AdminCtoEvent{"," let nf=a.bonding_curve.creator_fee_bps;let e=AdminCtoEvent{")]
G['tl_a_before_block']=[(" let (old_creator,old_fee)={\n"," let (old_creator,old_fee)={ \n")]
# v7c (w14a21-cto-helperbound #3273): validate body as an immediately-called capturing closure at the same lines
def _v7c(s):
    VL='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);'
    CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
    i=s.index(VL); j=s.index(' Ok(target)}pub fn execute('); k=s.index(CALL)
    body=s[i+len(VL):j]; head=s[j+len(' Ok(target)}'):k]
    op='let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);'
    return s[:i]+head+op+body+' Ok(target)})()?;'+s[k+len(CALL):]
G['v7c']=[_v7c]
# tail polarity knobs (06967d3)
G['pu_neg']=[("\n if pool_updated{\n","\n if !pool_updated{msg!(\"No canonical pump pool for this mint; curve only\");}else{\n"),("\n }else{msg!(\"No canonical pump pool for this mint; curve only\");}\n","\n }\n")]
G['sh_nonefirst']=[("\n match sharing_update{Some(val)=>{\n","\n match sharing_update{None=>{}Some(val)=>{\n"),("\n }None=>{}}\n","\n }}\n")]
G['sh_iflet']=[("\n match sharing_update{Some(val)=>{\n","\n if let Some(val)=sharing_update{{\n"),("\n }None=>{}}\n","\n }}\n")]
G['ev_reset_early']=[("\n match sharing_update{Some(val)=>{\n","\n let reset=sharing_update.is_some();match sharing_update{Some(val)=>{\n"),("sharing_config_reset:sharing_update.is_some(),","sharing_config_reset:reset,")]
G['sh_ref']=[("\n match sharing_update{Some(val)=>{\n","\n match &sharing_update{Some(val)=>{let val=*val;\n")]
