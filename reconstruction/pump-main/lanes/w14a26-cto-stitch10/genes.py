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
    raise KeyError(name)
def apply(s,names):
    n0=s.count('\n')
    for nm in names:
        for e in gene(nm):
            if callable(e): s=e(s); continue
            a,b=e; c=s.count(a); assert c==1,(nm,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,'newline count changed'
    return s
# AdminCtoEvent literal evaluation order
EVF=[('timestamp','Clock::get()?.unix_timestamp'),('authority','a.admin_set_creator_authority.key()'),('mint',None),('bonding_curve','a.bonding_curve.key()'),('old_creator',None),('new_creator','a.bonding_curve.creator'),('is_holder_reward','a.bonding_curve.is_holder_reward'),('is_cashback_coin','a.bonding_curve.is_cashback_coin'),('old_creator_fee_bps','old_fee'),('new_creator_fee_bps','nf'),('sharing_config_reset','sharing_update.is_some()'),('swept_to_holder_vault','swept'),('pool_updated',None)]
def _evlit(fs): return 'let e=AdminCtoEvent{'+','.join(n if v is None else f'{n}:{v}' for n,v in fs)+'};'
EVLIT=_evlit(EVF)
def evo(names):  # names: list of field names to move to the front in that order
    d=dict(EVF); fs=[(n,d[n]) for n in names]+[(n,v) for n,v in EVF if n not in names]
    return [(EVLIT,_evlit(fs))]
def evlast(names):
    d=dict(EVF); fs=[(n,v) for n,v in EVF if n not in names]+[(n,d[n]) for n in names]
    return [(EVLIT,_evlit(fs))]
G['evo_ts_last']=evlast(['timestamp'])
G['evo_ts_after_bc']=evo(['authority','mint','bonding_curve','timestamp'])
G['evo_bc_first']=evo(['bonding_curve'])
G['evo_mint_first']=evo(['mint'])
G['evo_curve_first']=evo(['new_creator','is_holder_reward','is_cashback_coin'])
G['evo_curve_ts']=evo(['new_creator','is_holder_reward','is_cashback_coin','timestamp'])
G['evo_old_first']=evo(['old_creator','old_creator_fee_bps'])
G['evo_auth_last']=evlast(['authority'])
G['evo_bc_last']=evlast(['bonding_curve'])
G['evo_nc_last']=evlast(['new_creator'])
G['evo_flags_first']=evo(['sharing_config_reset','swept_to_holder_vault','pool_updated'])
G['evo_hrcb_swap']=[("is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:a.bonding_curve.is_cashback_coin,is_holder_reward:a.bonding_curve.is_holder_reward,")]
G['evo_nf_before_old']=[("old_creator_fee_bps:old_fee,new_creator_fee_bps:nf,","new_creator_fee_bps:nf,old_creator_fee_bps:old_fee,")]
G['evo_nc_before_old']=[("old_creator,new_creator:a.bonding_curve.creator,","new_creator:a.bonding_curve.creator,old_creator,")]
