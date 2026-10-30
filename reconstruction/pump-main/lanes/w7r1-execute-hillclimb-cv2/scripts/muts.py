# Mutation catalog for create_v2::execute. Each entry: list of (old,new) exact replacements; newline count must be preserved.
SOLR=" if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None,QuoteSource::Sol));}"
SOLR2="  return Ok((Pubkey::default(),None,QuoteSource::Sol));"
M={}
def add(n,*pairs): M[n]=list(pairs)
# --- Sol early returns
add('sol_newarr',(SOLR,SOLR.replace('Pubkey::default()','Pubkey::new_from_array([0;32])')),(SOLR2,SOLR2.replace('Pubkey::default()','Pubkey::new_from_array([0;32])')))
add('sol_dflt',(SOLR,SOLR.replace('Pubkey::default()','Default::default()')),(SOLR2,SOLR2.replace('Pubkey::default()','Default::default()')))
add('sol_r1_let',(SOLR," if remaining_accounts.is_empty() {let sol=Pubkey::default();return Ok((sol,None,QuoteSource::Sol));}"))
add('sol_r2_let',(SOLR2,"  let sol=Pubkey::default();return Ok((sol,None,QuoteSource::Sol));"))
add('sol_r1_noret',(SOLR," if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None::<u64>,QuoteSource::Sol))}"))
add('sol_const',(SOLR,SOLR.replace('Ok((Pubkey::default(),None,QuoteSource::Sol))','Ok(SOL_QUOTE)')),(SOLR2,SOLR2.replace('Ok((Pubkey::default(),None,QuoteSource::Sol))','Ok(SOL_QUOTE)')),
    ("fn validate_quote_mint<'info>","const SOL_QUOTE:(Pubkey,Option<u64>,QuoteSource)=(Pubkey::new_from_array([0;32]),None,QuoteSource::Sol);fn validate_quote_mint<'info>"))
add('sol_helper',(SOLR,SOLR.replace('Ok((Pubkey::default(),None,QuoteSource::Sol))','sol_quote()')),(SOLR2,SOLR2.replace('Ok((Pubkey::default(),None,QuoteSource::Sol))','sol_quote()')),
    ("fn validate_quote_mint<'info>","fn sol_quote()->Result<(Pubkey,Option<u64>,QuoteSource)>{Ok((Pubkey::default(),None,QuoteSource::Sol))}fn validate_quote_mint<'info>"))
add('sol_r1_ifelse',(SOLR," if remaining_accounts.is_empty() {return Ok((Pubkey::default(),Option::None,QuoteSource::Sol));}"))
# --- execute destructure / call
DS=" let (quote_mint,reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;"
add('ds_ref',(DS," let (quote_mint,reserves,source)=validate_quote_mint(&ctx.accounts,ctx.remaining_accounts)?;"))
add('ds_a',(DS," let (quote_mint,reserves,source)=validate_quote_mint(a,ctx.remaining_accounts)?;"))
add('ds_q',(DS," let q=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;let (quote_mint,reserves,source)=q;"))
add('ds_mut',(DS," let (quote_mint,mut reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;"))
# --- depth
DP=" let depth=match source {QuoteSource::Sol|QuoteSource::Whitelisted|QuoteSource::Controlled=>0,QuoteSource::Nested(depth)=>depth};"
add('dp_iflet',(DP," let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};"))
add('dp_wild',(DP," let depth=match source {QuoteSource::Nested(depth)=>depth,_=>0};"))
add('dp_first',(DP," let depth=match source {QuoteSource::Nested(depth)=>depth,QuoteSource::Sol|QuoteSource::Whitelisted|QuoteSource::Controlled=>0};"))
# --- init_curve call
IC=" init_curve(&mut ctx.accounts.bonding_curve,&ctx.accounts.global,creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);"
add('ic_deref',(IC," init_curve(&mut *ctx.accounts.bonding_curve,&ctx.accounts.global,creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);"))
add('ic_glob_a',(IC," init_curve(&mut ctx.accounts.bonding_curve,&a.global,creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);"))
# --- validate_metadata call
VM=" validate_metadata(&name,&symbol,&uri)?;\n let a=&ctx.accounts;"
add('vm_asstr',(VM," validate_metadata(name.as_str(),symbol.as_str(),uri.as_str())?;\n let a=&ctx.accounts;"))
add('vm_swap',(VM," let a=&ctx.accounts;\n validate_metadata(&name,&symbol,&uri)?;"))
# --- init_curve body
add('icb_sol_inline',(" let sol=Pubkey::default();\n let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n let virtual_quote_reserves=if quote_mint==sol {",
   "\n let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n let virtual_quote_reserves=if quote_mint==Pubkey::default() {"))
add('icb_unwrap_else',("reserves.unwrap_or(initial_virtual_quote_reserves)","reserves.unwrap_or_else(||initial_virtual_quote_reserves)"))
add('icb_match',("reserves.unwrap_or(initial_virtual_quote_reserves)","match reserves {Some(r)=>r,None=>initial_virtual_quote_reserves}"))
def apply(t,names):
    for n in names:
        for o,nw in M[n]:
            if t.count(o)!=1: raise ValueError(f'{n}: {t.count(o)} hits for {o[:60]!r}')
            if o.count('\n')!=nw.count('\n') and not o.startswith('fn '): raise ValueError(f'{n}: newline change')
            t=t.replace(o,nw)
    return t
# --- creator store position in init_curve
_IC_STORES=[" bonding_curve.initial_virtual_quote_reserves=virtual_quote_reserves;"," bonding_curve.virtual_token_reserves=global.initial_virtual_token_reserves;"," bonding_curve.virtual_quote_reserves=virtual_quote_reserves;"," bonding_curve.real_token_reserves=global.initial_real_token_reserves;"," bonding_curve.real_quote_reserves=0;"," bonding_curve.token_total_supply=global.token_total_supply;"," bonding_curve.is_mayhem_mode=is_mayhem_mode;"," bonding_curve.is_cashback_coin=false;"," bonding_curve.quote_mint=quote_mint;"," bonding_curve.creator_fee_bps=fee;"," bonding_curve.can_edit_creator_fee=false;"," bonding_curve.is_holder_reward=is_holder_reward;"," bonding_curve.depth=depth;"," bonding_curve.post_complete_base_out=0;"," bonding_curve.post_complete_quote_in=0;"]
CR=" bonding_curve.creator=creator;\n"
for i,s in enumerate(_IC_STORES):
    if i==5: continue
    M[f'cr_after{i}']=[('FUNC',('creator_after',s))]
_apply_plain=None
def _creator_after(t,s):
    a=t.index('fn init_curve(')
    body=t[a:]
    body2=body.replace(CR,'',1)
    body2=body2.replace(s+'\n',s+'\n'+CR,1)
    return t[:a]+body2
# --- tuple order permutations of validate_quote_mint result
import itertools
def _perm(t,p):
    names=['Pubkey','Option<u64>','QuoteSource']
    sig="->Result<(Pubkey,Option<u64>,QuoteSource)>{"
    t=t.replace(sig,"->Result<("+','.join(names[i] for i in p)+")>{",1)
    def fx(vals): return '('+','.join(vals[i] for i in p)+')'
    t=t.replace("Ok((Pubkey::default(),None,QuoteSource::Sol))","Ok("+fx(['Pubkey::default()','None','QuoteSource::Sol'])+")")
    t=t.replace("Ok((mint_key,reserves,source))","Ok("+fx(['mint_key','reserves','source'])+")")
    t=t.replace("let (quote_mint,reserves,source)=validate_quote_mint","let "+fx(['quote_mint','reserves','source'])+"=validate_quote_mint")
    return t
for p in itertools.permutations(range(3)):
    if p==(0,1,2): continue
    M['perm'+''.join(map(str,p))]=[('FUNC',('perm',p))]
# --- attrs
add('vm_inl_always',("fn validate_metadata(name:&str","#[inline(always)] fn validate_metadata(name:&str"))
add('vm_inl',("fn validate_metadata(name:&str","#[inline] fn validate_metadata(name:&str"))
add('ic_inl_always',("fn init_curve(bonding_curve","#[inline(always)] fn init_curve(bonding_curve"))
add('ic_inl',("fn init_curve(bonding_curve","#[inline] fn init_curve(bonding_curve"))
add('vqm_inl_always',("fn validate_quote_mint<'info>","#[inline(always)] fn validate_quote_mint<'info>"))
add('vqm_inl',("fn validate_quote_mint<'info>","#[inline] fn validate_quote_mint<'info>"))
# --- validate_metadata before init_curve (swap the two statement lines)
add('vm_before_ic',(IC+"\n",""),(VM," validate_metadata(&name,&symbol,&uri)?;\n let a=&ctx.accounts;"),)
_old_apply=apply
def apply(t,names):
    for n in names:
        if n=='vm_before_ic':
            i=t.index(IC); line=IC
            t=t.replace(IC+'\n','\n',1)
            t=t.replace(" validate_metadata(&name,&symbol,&uri)?;\n"," validate_metadata(&name,&symbol,&uri)?;"+line+"\n",1)
            continue
        e=M[n]
        if e and e[0][0]=='FUNC':
            k,arg=e[0][1]
            t2=_creator_after(t,arg) if k=='creator_after' else _perm(t,arg)
            if t2.count('\n')!=t.count('\n'): raise ValueError('newline change')
            t=t2; continue
        t=_old_apply(t,[n])
    return t
# ---- batch h3
IM=" initialize_metadata(&ctx,name.clone(),symbol.clone(),uri.clone())?;"
add('im_toowned',(IM," initialize_metadata(&ctx,name.to_owned(),symbol.to_owned(),uri.to_owned())?;"))
add('im_tuple',(IM," let (n,s,u)=(name.clone(),symbol.clone(),uri.clone());initialize_metadata(&ctx,n,s,u)?;"))
add('im_ctxref',(IM," initialize_metadata(&ctx,String::clone(&name),String::clone(&symbol),String::clone(&uri))?;"))
CE=" let event=create_event(name,symbol,uri,creator,&a.mint,&a.user,&a.bonding_curve,&a.token_program,is_mayhem_mode,fee)?;"
add('ce_noa',(VM," validate_metadata(&name,&symbol,&uri)?;\n"),(CE," let a=&ctx.accounts;let event=create_event(name,symbol,uri,creator,&a.mint,&a.user,&a.bonding_curve,&a.token_program,is_mayhem_mode,fee)?;"))
add('ce_ctx',(CE," let event=create_event(name,symbol,uri,creator,&ctx.accounts.mint,&ctx.accounts.user,&ctx.accounts.bonding_curve,&ctx.accounts.token_program,is_mayhem_mode,fee)?;"))
add('ce_emit_ref',(" emit!(event);emit_cpi!(event);Ok(())"," emit!(event);emit_cpi!(event);return Ok(());"))
MY=" if is_mayhem_mode { initialize_mayhem(&ctx)?; }"
add('my_ret',(MY," if is_mayhem_mode { initialize_mayhem(&ctx)? }"))
# validate_metadata alternate checks
VMB=" require_gte!(MAX_NAME_LENGTH,name.len(),PumpError::NameTooLong);"
add('vmb_len_let',(" fn validate_metadata(name:&str,symbol:&str,uri:&str)->Result<()>{\n"+VMB," fn validate_metadata(name:&str,symbol:&str,uri:&str)->Result<()>{\n let name_len=name.len();require_gte!(MAX_NAME_LENGTH,name_len,PumpError::NameTooLong);")) if False else None
add('vm_string',("fn validate_metadata(name:&str,symbol:&str,uri:&str)->Result<()>{","fn validate_metadata(name:&String,symbol:&String,uri:&String)->Result<()>{"))
add('vm_slices',(" validate_metadata(&name,&symbol,&uri)?;"," validate_metadata(&name[..],&symbol[..],&uri[..])?;"))
add('vm_qmark_match',(" validate_metadata(&name,&symbol,&uri)?;"," match validate_metadata(&name,&symbol,&uri){Ok(())=>{},Err(e)=>return Err(e)}"))
# init_curve: sol compare forms
SC=" let virtual_quote_reserves=if quote_mint==sol {"
add('sc_eq',(SC," let virtual_quote_reserves=if quote_mint.eq(&sol) {"))
add('sc_rev',(SC," let virtual_quote_reserves=if sol==quote_mint {"))
add('sc_ne',(SC+"global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};"," let virtual_quote_reserves=if quote_mint!=sol {reserves.unwrap_or(initial_virtual_quote_reserves)} else {global.initial_virtual_sol_reserves};"))
add('sc_match',(SC+"global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};"," let virtual_quote_reserves=match (quote_mint==sol,reserves) {(true,_)=>global.initial_virtual_sol_reserves,(false,Some(r))=>r,(false,None)=>initial_virtual_quote_reserves};"))
add('sc_ivqr_late',(" let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n"+SC+"global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};",
    "\n"+SC+"global.initial_virtual_sol_reserves} else {reserves.unwrap_or(global.initial_virtual_quote_reserves)};"))
add('sc_sol_after_ivqr',(" let sol=Pubkey::default();\n let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;"," let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n let sol=Pubkey::default();"))
add('sc_is_sol_param',(SC," let virtual_quote_reserves=if quote_mint==sol as Pubkey {"))
# depth/fee
FE=" let fee=if matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) && creator_fee_bps.0>0 {"
add('fe_ne0',(FE,FE.replace('creator_fee_bps.0>0','creator_fee_bps.0!=0')))
add('fe_swap',(FE," let fee=if creator_fee_bps.0>0 && matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) {"))
add('fe_match',(FE," let fee=if match source {QuoteSource::Controlled|QuoteSource::Nested(_)=>true,_=>false} && creator_fee_bps.0>0 {"))
add('fe_bps_let',(FE," let bps=creator_fee_bps.0;let fee=if matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_)) && bps>0 {"))
add('dp_before_fee',(DP+"\n",""+"\n"),(FE,DP+FE))
# creator
add('cr_match',(" let creator=if is_holder_reward.0 {"," let creator=if is_holder_reward.0==true {"))
add('ic_cr_ref',(IC,IC.replace('init_curve(&mut ctx.accounts.bonding_curve,','init_curve(&mut ctx.accounts.bonding_curve as &mut trade_types::BondingCurve,')))
add('ic_bc_let',(IC," let bc:&mut trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;init_curve(bc,&ctx.accounts.global,creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);"))
add('ic_hr_let',(IC,IC.replace('is_holder_reward.0);','{is_holder_reward.0});')))
# ---- struct return with explicit field order (repr C / Rust)
FIELDS={'m':('mint','Pubkey'),'r':('reserves','Option<u64>'),'s':('source','QuoteSource')}
def _struct(t,order,repr):
    decl=f"{repr}struct QuoteInfo{{"+','.join(f'{FIELDS[c][0]}:{FIELDS[c][1]}' for c in order)+"}"
    t=t.replace("pub enum QuoteSource { Sol, Whitelisted, Controlled, Nested(u8) }","pub enum QuoteSource { Sol, Whitelisted, Controlled, Nested(u8) }"+decl,1)
    t=t.replace("->Result<(Pubkey,Option<u64>,QuoteSource)>{","->Result<QuoteInfo>{",1)
    t=t.replace("Ok((Pubkey::default(),None,QuoteSource::Sol))","Ok(QuoteInfo{mint:Pubkey::default(),reserves:None,source:QuoteSource::Sol})")
    t=t.replace("Ok((mint_key,reserves,source))","Ok(QuoteInfo{mint:mint_key,reserves,source})")
    t=t.replace("let (quote_mint,reserves,source)=validate_quote_mint","let QuoteInfo{mint:quote_mint,reserves,source}=validate_quote_mint")
    return t
for p in itertools.permutations('mrs'):
    for rp,tag in (('#[repr(C)]','c'),('','r')):
        M['st'+tag+''.join(p)]=[('FUNC',('struct',(''.join(p),rp)))]
def apply(t,names,_prev=apply):
    for n in names:
        e=M[n]
        if e and e[0][0]=='FUNC' and e[0][1][0]=='struct':
            o,rp=e[0][1][1]; t2=_struct(t,o,rp)
            if t2.count('\n')!=t.count('\n'): raise ValueError('nl')
            t=t2; continue
        t=_prev(t,[n])
    return t
# ---- h5: init_curve branch-probability / compare forms
VQ=" let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};"
def vq(n,new): add(n,(VQ,new))
vq('vq_tobytes'," let virtual_quote_reserves=if quote_mint.to_bytes()==sol.to_bytes() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};")
vq('vq_asref'," let virtual_quote_reserves=if quote_mint.as_ref()==sol.as_ref() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};")
vq('vq_refeq'," let virtual_quote_reserves=if &quote_mint==&sol {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};")
vq('vq_none_first'," let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else {match reserves {None=>initial_virtual_quote_reserves,Some(r)=>r}};")
vq('vq_iflet'," let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else if let Some(r)=reserves {r} else {initial_virtual_quote_reserves};")
vq('vq_mapor'," let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else {reserves.map_or(initial_virtual_quote_reserves,|r|r)};")
vq('vq_issome'," let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else if reserves.is_some() {reserves.unwrap()} else {initial_virtual_quote_reserves};")
vq('vq_isnone'," let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else if reserves.is_none() {initial_virtual_quote_reserves} else {reserves.unwrap()};")
vq('vq_unwrap_or_default'," let virtual_quote_reserves=if quote_mint==sol {global.initial_virtual_sol_reserves} else {reserves.or(Some(initial_virtual_quote_reserves)).unwrap()};")
vq('vq_match_all'," let virtual_quote_reserves=match reserves {_ if quote_mint==sol=>global.initial_virtual_sol_reserves,Some(r)=>r,None=>initial_virtual_quote_reserves};")
vq('vq_ret_block'," let virtual_quote_reserves={if quote_mint==sol {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)}};")
vq('vq_let_else'," let virtual_quote_reserves=if quote_mint!=sol {reserves.unwrap_or(initial_virtual_quote_reserves)} else {global.initial_virtual_sol_reserves};")
vq('vq_sol_ref'," let virtual_quote_reserves=if quote_mint.eq(&Pubkey::default()) {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};")
vq('vq_bool'," let is_sol=quote_mint==sol;let virtual_quote_reserves=if is_sol {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(initial_virtual_quote_reserves)};")
# ---- h6: consuming the validate_quote_mint result
VC="validate_quote_mint(ctx.accounts,ctx.remaining_accounts)"
DS2=" let (quote_mint,reserves,source)="+VC+"?;"
add('vc_match',(DS2," let (quote_mint,reserves,source)=match "+VC+" {Ok(v)=>v,Err(e)=>return Err(e)};"))
add('vc_match_err_first',(DS2," let (quote_mint,reserves,source)=match "+VC+" {Err(e)=>return Err(e),Ok(v)=>v};"))
add('vc_match_destr',(DS2," let (quote_mint,reserves,source)=match "+VC+" {Ok((q,r,s))=>(q,r,s),Err(e)=>return Err(e)};"))
add('vc_mapErr',(DS2," let (quote_mint,reserves,source)="+VC+".map_err(|e|e)?;"))
add('vc_into',(DS2," let (quote_mint,reserves,source)="+VC+".map_err(Into::<anchor_lang::error::Error>::into)?;"))
add('vc_letelse',(DS2," let r="+VC+";let Ok((quote_mint,reserves,source))=r else {return Err(r.err().unwrap())};"))
add('vc_iflet',(DS2," let r="+VC+";if let Err(e)=r {return Err(e)};let (quote_mint,reserves,source)=r.unwrap();"))
add('vc_q_sep',(DS2," let res="+VC+";let (quote_mint,reserves,source)=res?;"))
add('vc_q_fields',(DS2," let q="+VC+"?;let quote_mint=q.0;let reserves=q.1;let source=q.2;"))
add('vc_q_fields_rev',(DS2," let q="+VC+"?;let source=q.2;let reserves=q.1;let quote_mint=q.0;"))
add('vc_q_ref',(DS2," let q=&"+VC+"?;let (quote_mint,reserves,source)=(q.0,q.1,q.2);"))
# ---- h7: Pubkey flow through the result (SROA promotion order of the word0 slice)
RET=" Ok((mint_key,reserves,source))"
add('rk_minkey',(RET," Ok((mint.key(),reserves,source))"))
add('rk_deref',(RET," Ok((*mint.key,reserves,source))"))
add('rk_bytes',(RET," Ok((Pubkey::new_from_array(mint_key.to_bytes()),reserves,source))"))
add('rk_clone',(RET," Ok((mint_key.clone(),reserves,source))"))
add('rk_let',(RET," let quote=(mint_key,reserves,source);Ok(quote)"))
add('mk_deref',(" let mint_key=mint.key();"," let mint_key=*mint.key;"))
add('mk_ref',(" let mint_key=mint.key();"," let mint_key=*mint.unsigned_key();"))
SOLB=" if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None,QuoteSource::Sol));}"
add('sol1_bytes',(SOLB," if remaining_accounts.is_empty() {return Ok((Pubkey::new_from_array([0u8;32]),None,QuoteSource::Sol));}"),(SOLR2,"  return Ok((Pubkey::new_from_array([0u8;32]),None,QuoteSource::Sol));"))
add('sol_native_mint',(SOLR2,"  return Ok((Pubkey::default(),Option::<u64>::None,QuoteSource::Sol));"))
add('ex_qm_copy',(DS2," let (quote_mint,reserves,source)="+VC+"?;let quote_mint:Pubkey=quote_mint;"))
GQ="crate::pump_quote::global_quote(quote_mint,&a.global)"
add('ex_gq_clone',(GQ,"crate::pump_quote::global_quote(quote_mint.clone(),&a.global)"))
# ---- h8: Sol-return zero source forms (aim: avoid memset over the ptr-typed word0 slice)
def solall(n,expr,extra=None):
    pairs=[(SOLR,SOLR.replace('Ok((Pubkey::default(),None,QuoteSource::Sol))',expr)),(SOLR2,SOLR2.replace('Ok((Pubkey::default(),None,QuoteSource::Sol))',expr))]
    if extra: pairs.append(("fn validate_quote_mint<'info>",extra+"fn validate_quote_mint<'info>"))
    M[n]=pairs
solall('z_static','Ok((ZERO_KEY,None,QuoteSource::Sol))',"static ZERO_KEY:Pubkey=Pubkey::new_from_array([0;32]);")
solall('z_static_ref','Ok((*&ZERO_KEY,None,QuoteSource::Sol))',"static ZERO_KEY:Pubkey=Pubkey::new_from_array([0;32]);")
solall('z_tuple_default','Ok(Default::default())')
solall('z_src_default','Ok((Pubkey::default(),None,Default::default()))')
solall('z_static_tuple','Ok(SOL_QUOTE)',"static SOL_QUOTE:(Pubkey,Option<u64>,QuoteSource)=(Pubkey::new_from_array([0;32]),None,QuoteSource::Sol);")
solall('z_newunique','Ok((Pubkey::from([0u8;32]),None,QuoteSource::Sol))')
solall('z_try_from','Ok((Pubkey::try_from([0u8;32].as_slice()).unwrap(),None,QuoteSource::Sol))')
solall('z_word_split','Ok((Pubkey::new_from_array(zero_key()),None,QuoteSource::Sol))',"fn zero_key()->[u8;32]{let mut k=[0u8;32];k[..8].copy_from_slice(&0u64.to_le_bytes());k}")
# ---- h9: init_curve parameter passing modes
ICS="fn init_curve(bonding_curve:&mut trade_types::BondingCurve,global:&Global,creator:Pubkey,quote_mint:Pubkey,reserves:Option<u64>,depth:u8,fee:u64,is_mayhem_mode:bool,is_holder_reward:bool){"
ICC=" init_curve(&mut ctx.accounts.bonding_curve,&ctx.accounts.global,creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);"
add('pc_cref',(ICS,ICS.replace('creator:Pubkey','creator:&Pubkey')),(ICC,ICC.replace(',creator,',',&creator,')),(" bonding_curve.creator=creator;"," bonding_curve.creator=*creator;"))
add('pc_qref',(ICS,ICS.replace('quote_mint:Pubkey','quote_mint:&Pubkey')),(ICC,ICC.replace(',quote_mint,',',&quote_mint,')),(" bonding_curve.quote_mint=quote_mint;"," bonding_curve.quote_mint=*quote_mint;"),("if quote_mint==sol {","if *quote_mint==sol {"))
add('pc_bothref',(ICS,ICS.replace('quote_mint:Pubkey','quote_mint:&Pubkey').replace('creator:Pubkey','creator:&Pubkey')),(ICC,ICC.replace(',quote_mint,',',&quote_mint,').replace(',creator,',',&creator,')),(" bonding_curve.quote_mint=quote_mint;"," bonding_curve.quote_mint=*quote_mint;"),("if quote_mint==sol {","if *quote_mint==sol {"),(" bonding_curve.creator=creator;"," bonding_curve.creator=*creator;"))
add('pc_rref',(ICS,ICS.replace('reserves:Option<u64>','reserves:&Option<u64>')),(ICC,ICC.replace(',reserves,',',&reserves,')),("reserves.unwrap_or(initial_virtual_quote_reserves)","reserves.unwrap_or(initial_virtual_quote_reserves)"))
add('pc_qref_cmp',(ICS,ICS.replace('quote_mint:Pubkey','quote_mint:&Pubkey')),(ICC,ICC.replace(',quote_mint,',',&quote_mint,')),(" bonding_curve.quote_mint=quote_mint;"," bonding_curve.quote_mint=*quote_mint;"),("if quote_mint==sol {","if quote_mint==&sol {"))
add('pc_sol_param',(ICS,ICS.replace('quote_mint:Pubkey,','quote_mint:Pubkey,').replace('{','{',1)),(" let sol=Pubkey::default();"," let sol:Pubkey=Default::default();"))
add('pc_glob_val',(ICC,ICC.replace('&ctx.accounts.global,','&*ctx.accounts.global,')))
add('pc_bc_acc',(ICS,ICS.replace('bonding_curve:&mut trade_types::BondingCurve','bonding_curve:&mut Account<trade_types::BondingCurve>')))
add('pc_args_order',(ICS,"fn init_curve(bonding_curve:&mut trade_types::BondingCurve,global:&Global,quote_mint:Pubkey,creator:Pubkey,reserves:Option<u64>,depth:u8,fee:u64,is_mayhem_mode:bool,is_holder_reward:bool){"),(ICC,ICC.replace('creator,quote_mint,','quote_mint,creator,')))
# ---- h10: by-ref consumers (alter SROA promotion order of the result slices)
add('sr_fee',("matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_))","matches!(&source,QuoteSource::Controlled|QuoteSource::Nested(_))"))
add('sr_depth',(" let depth=match source {"," let depth=match &source {"),("QuoteSource::Nested(depth)=>depth};","QuoteSource::Nested(depth)=>*depth};"))
add('sr_depth_ref',(" let depth=match source {"," let depth=match source {"),("QuoteSource::Nested(depth)=>depth};","QuoteSource::Nested(ref depth)=>*depth};"))
add('rr_opt_asref',(ICC,ICC.replace(',reserves,',',reserves.as_ref().copied(),')))
add('rr_opt_copied',(ICS,ICS.replace('reserves:Option<u64>','reserves:Option<&u64>')),(ICC,ICC.replace(',reserves,',',reserves.as_ref(),')),("reserves.unwrap_or(initial_virtual_quote_reserves)","reserves.copied().unwrap_or(initial_virtual_quote_reserves)"))
add('rr_opt_deref',(ICS,ICS.replace('reserves:Option<u64>','reserves:&Option<u64>')),(ICC,ICC.replace(',reserves,',',&reserves,')),("reserves.unwrap_or(initial_virtual_quote_reserves)","(*reserves).unwrap_or(initial_virtual_quote_reserves)"))
add('rr_opt_ref_match',(ICS,ICS.replace('reserves:Option<u64>','reserves:&Option<u64>')),(ICC,ICC.replace(',reserves,',',&reserves,')),("reserves.unwrap_or(initial_virtual_quote_reserves)","match reserves {Some(r)=>*r,None=>initial_virtual_quote_reserves}"))
# ---- h11: Sol encoded as None in the result, defaulted in execute
SIG="->Result<(Pubkey,Option<u64>,QuoteSource)>{"
def _optres(t,kind):
    if kind=='outer':
        t=t.replace(SIG,"->Result<Option<(Pubkey,Option<u64>,QuoteSource)>>{",1)
        t=t.replace("Ok((Pubkey::default(),None,QuoteSource::Sol))","Ok(None)")
        t=t.replace("Ok((mint_key,reserves,source))","Ok(Some((mint_key,reserves,source)))")
        t=t.replace("let (quote_mint,reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;","let (quote_mint,reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?.unwrap_or((Pubkey::default(),None,QuoteSource::Sol));")
    elif kind=='outer_else':
        t=t.replace(SIG,"->Result<Option<(Pubkey,Option<u64>,QuoteSource)>>{",1)
        t=t.replace("Ok((Pubkey::default(),None,QuoteSource::Sol))","Ok(None)")
        t=t.replace("Ok((mint_key,reserves,source))","Ok(Some((mint_key,reserves,source)))")
        t=t.replace("let (quote_mint,reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;","let (quote_mint,reserves,source)=match validate_quote_mint(ctx.accounts,ctx.remaining_accounts)? {Some(q)=>q,None=>(Pubkey::default(),None,QuoteSource::Sol)};")
    elif kind=='optkey':
        t=t.replace(SIG,"->Result<(Option<Pubkey>,Option<u64>,QuoteSource)>{",1)
        t=t.replace("Ok((Pubkey::default(),None,QuoteSource::Sol))","Ok((None,None,QuoteSource::Sol))")
        t=t.replace("Ok((mint_key,reserves,source))","Ok((Some(mint_key),reserves,source))")
        t=t.replace("let (quote_mint,reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;","let (quote_mint,reserves,source)=validate_quote_mint(ctx.accounts,ctx.remaining_accounts)?;let quote_mint=quote_mint.unwrap_or_default();")
    return t
for k in ('outer','outer_else','optkey'): M['or_'+k]=[('FUNC',('optres',k))]
def apply(t,names,_prev=apply):
    for n in names:
        e=M[n]
        if e and e[0][0]=='FUNC' and e[0][1][0]=='optres':
            t2=_optres(t,e[0][1][1])
            if t2.count('\n')!=t.count('\n'): raise ValueError('nl')
            t=t2; continue
        t=_prev(t,[n])
    return t
# ---- h12: merge the Ok values into one return (Sol pubkey reaches the sret via memcpy, not memset)
VQS="fn validate_quote_mint<'info>(accounts:&CreateV2<'info>,remaining_accounts:&[AccountInfo<'info>])->Result<(Pubkey,Option<u64>,QuoteSource)>{\n"
def lbl(n,first,second,last):
    M[n]=[(VQS+SOLR+"\n",VQS+first+"\n"),(SOLR2,second),("\n Ok((mint_key,reserves,source))\n}","\n "+last+"\n}")]
lbl('lb_all'," let quote='q:{if remaining_accounts.is_empty() {break 'q (Pubkey::default(),None,QuoteSource::Sol);}","  break 'q (Pubkey::default(),None,QuoteSource::Sol);","(mint_key,reserves,source)};Ok(quote)")
lbl('lb_all_ret'," let quote='q:{if remaining_accounts.is_empty() {break 'q (Pubkey::default(),None,QuoteSource::Sol);}","  break 'q (Pubkey::default(),None,QuoteSource::Sol);","(mint_key,reserves,source)};return Ok(quote);")
lbl('lb_first'," let quote='q:{if remaining_accounts.is_empty() {break 'q (Pubkey::default(),None,QuoteSource::Sol);}","  return Ok((Pubkey::default(),None,QuoteSource::Sol));","(mint_key,reserves,source)};Ok(quote)")
lbl('lb_key_only'," let (mint_key,reserves,source)='q:{if remaining_accounts.is_empty() {break 'q (Pubkey::default(),None,QuoteSource::Sol);}","  break 'q (Pubkey::default(),None,QuoteSource::Sol);","(mint_key,reserves,source)};Ok((mint_key,reserves,source))")
# ---- h15: wrapper returning the inner result (outer SROA splits the Sol pubkey word0 from the 24-byte tail)
VQN="fn validate_quote_mint<'info>(accounts:&CreateV2<'info>,remaining_accounts:&[AccountInfo<'info>])->Result<(Pubkey,Option<u64>,QuoteSource)>{"
def wrap(n,body,attr=''):
    M[n]=[(VQN,attr+"fn validate_quote_mint<'info>(accounts:&CreateV2<'info>,remaining_accounts:&[AccountInfo<'info>])->Result<(Pubkey,Option<u64>,QuoteSource)>{"+body+"}fn validate_quote_mint_inner<'info>(accounts:&CreateV2<'info>,remaining_accounts:&[AccountInfo<'info>])->Result<(Pubkey,Option<u64>,QuoteSource)>{")]
wrap('wr_q',"let (q,r,s)=validate_quote_mint_inner(accounts,remaining_accounts)?;Ok((q,r,s))")
wrap('wr_v',"let v=validate_quote_mint_inner(accounts,remaining_accounts)?;Ok(v)")
wrap('wr_pass',"validate_quote_mint_inner(accounts,remaining_accounts)")
wrap('wr_match',"match validate_quote_mint_inner(accounts,remaining_accounts){Ok((q,r,s))=>Ok((q,r,s)),Err(e)=>Err(e)}")
wrap('wr_map',"validate_quote_mint_inner(accounts,remaining_accounts).map(|(q,r,s)|(q,r,s))")
# ---- h16: Sol return copies the default-compare temp
NB=" if mint_key==anchor_spl::token::spl_token::native_mint::ID || mint_key==Pubkey::default() {\n  return Ok((Pubkey::default(),None,QuoteSource::Sol));"
add('sl_native'," ".join([]) and None or (NB," let sol=Pubkey::default();if mint_key==anchor_spl::token::spl_token::native_mint::ID || mint_key==sol {\n  return Ok((sol,None,QuoteSource::Sol));"))
add('sl_native_ref',(NB," let sol=Pubkey::default();if mint_key==anchor_spl::token::spl_token::native_mint::ID || &mint_key==&sol {\n  return Ok((sol,None,QuoteSource::Sol));"))
add('sl_native_eq',(NB," let sol=Pubkey::default();if mint_key==anchor_spl::token::spl_token::native_mint::ID || mint_key.eq(&sol) {\n  return Ok((sol,None,QuoteSource::Sol));"))
add('sl_both',(NB," if mint_key==anchor_spl::token::spl_token::native_mint::ID || mint_key==sol {\n  return Ok((sol,None,QuoteSource::Sol));"),(SOLR," let sol=Pubkey::default();if remaining_accounts.is_empty() {return Ok((sol,None,QuoteSource::Sol));}"))
add('sl_mintkey',(NB," if mint_key==anchor_spl::token::spl_token::native_mint::ID || mint_key==Pubkey::default() {\n  let mint_key=Pubkey::default();return Ok((mint_key,None,QuoteSource::Sol));"))
