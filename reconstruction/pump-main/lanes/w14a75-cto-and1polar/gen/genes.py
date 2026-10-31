# Gene library (experiment only): w14a39 genes.py + w14a75 additions. Each G[name] is a list of exact (old,new) source edits
# on programs/pump/src/creator/admin_cto.rs at main 0d04cf4. B = p3u+tu8 (the and-1 holder + and-1 306 tag basin).
_QL='a.global.whitelisted_quote_mints.contains(&q)};let (holder,cashback,target,sharing_update,collect_old,skip)={'
_EH='let hopt=holder;let holder=hopt==Some(true);'
_VH='->Result<Pubkey>{let holder=hopt==Some(true);'
_289='&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
_T306='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
_EX='->Result<()>{ let a=&ctx.accounts;'
G={}
_VBU=[('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:u8,'),(_VH,'->Result<Pubkey>{let holder=hopt&1!=0;'),(_289,'&&hopt&1==0{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
_VB=[('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:bool,'),(_VH,'->Result<Pubkey>{let holder=hopt;'),(_289,'&&!hopt{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
_EH3=(_EH,'let hopt=hb;let holder=hb;')
G['p3u']=[(_QL,_QL[:-len('let (holder,cashback,target,sharing_update,collect_old,skip)={')]+'let hb=holder.unwrap_or(false);let (holder,cashback,target,sharing_update,collect_old,skip)={'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['p3n']=[(_QL,_QL[:-len('let (holder,cashback,target,sharing_update,collect_old,skip)={')]+'let hb=holder.unwrap_or(false);let (holder,cashback,target,sharing_update,collect_old,skip)={'),_EH3]+_VB
G['p2']=[('holder_key=hk.0;','holder_key=hk.0;let hb=holder.unwrap_or(false);'),_EH3]+_VB
G['p2u']=[('holder_key=hk.0;','holder_key=hk.0;let hb=holder.unwrap_or(false);'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['p1']=[('let mint=a.mint.key();','let mint=a.mint.key();let hb=holder.unwrap_or(false);'),_EH3]+_VB
G['p1u']=[('let mint=a.mint.key();','let mint=a.mint.key();let hb=holder.unwrap_or(false);'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['e3']=[(_EX,'->Result<()>{ let hb=holder.unwrap_or(false);let a=&ctx.accounts;'),(_EH,'let hopt=hb;let holder=hb;')]+_VB
G['p0u']=[(_EX,'->Result<()>{ let hb=holder.unwrap_or(false);let a=&ctx.accounts;'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['tu8']=[(_T306,'let t=if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{unsafe{new.unwrap_unchecked()}}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
def mk(*n):
    E=[]
    for x in n: E+=G[x]
    return E
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
HK0='let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'
ARGS='let args=&(new,);'
VAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
STE='fee_configurable:a.global.creator_fee_configurable};'
SIG='new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
HARM='CtoNewCreatorNotAllowed));}*holder_key}else{'
CMP='if t==*sharing||t==*holder_key{'
def val(newx='new',hk='&holder_key',sk='&sk'):
    return 'let mut target=validate(&st,hopt,fee,%s,%s,%s)?;'%(newx,hk,sk)
G['V2']=[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==sharing||t==holder_key{'),(VAL,val('new','holder_key','sk'))]
G['V1']=[(SIG,'new:Option<Pubkey>,holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),(HARM,'CtoNewCreatorNotAllowed));}holder_key}else{'),(CMP,'if t==*sharing||t==holder_key{'),(VAL,val('new','holder_key','&sk'))]
G['AC']=[(ARGS,''),(STE,STE+ARGS)]
G['AV']=[(lambda s:s.replace('let mut target=validate(&st,hopt,fee,new,','let mut target=validate(&st,hopt,fee,args.0,',1))]
G['HK0']=[(HK,HK0)]
import re as _re
def _lits(s): return list(_re.finditer(r'AccountInfo\{([^{}]*)\}',s))
def rcswap(k):
    def f(s):
        m=_lits(s)[k]; body=m.group(1)
        a=_re.search(r'lamports:[^,]*?\.lamports\.clone\(\)',body).group(0); b=_re.search(r'data:[^,]*?\.data\.clone\(\)',body).group(0)
        nb=body.replace(a,'\0A').replace(b,a).replace('\0A',b)
        return s[:m.start(1)]+nb+s[m.end(1):]
    return f
for _k in range(12): G['RC%d'%_k]=[rcswap(_k)]
import json as _j
for _k in _j.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    if _k.get('edit'): G['K_'+_k['name']]=[(e['old'],e['new']) for e in _k['edit']]
def _lit(src,order):
    f={'K':'key:x.key','L':'lamports:x.lamports.clone()','D':'data:x.data.clone()','O':'owner:x.owner','R':'rent_epoch:x.rent_epoch','S':'is_signer:x.is_signer','W':'is_writable:x.is_writable','E':'executable:x.executable'}
    return '{let x:&AccountInfo='+src+';AccountInfo{'+','.join(f[c] for c in order)+'}}'
_TCF={'ata':('associated_token_program:a.associated_token_program.to_account_info(),coin_creator:','a.associated_token_program.as_ref()'),
      'cc':('_token_program:a.associated_token_program.to_account_info(),coin_creator:a.current_creator.to_account_info(),','&a.current_creator'),
      'cva':('coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:{','a.coin_creator_vault_authority.as_ref()')}
def tl(name,order):
    old,src=_TCF[name]
    if name=='cc': return [(old,'_token_program:a.associated_token_program.to_account_info(),coin_creator:'+_lit(src,order)+',')]
    fld=old.split(':')[0]; tail=old[old.index('.to_account_info()')+len('.to_account_info()'):]
    return [(old,fld+':'+_lit(src,order)+tail)]
for _n in _TCF:
    G['TL_'+_n]=tl(_n,'KODLRSWE'.replace('D','').replace('O','')[:0] or 'KLDORSWE')
    G['TLO_'+_n]=tl(_n,'KOLDRSWE')
_F338='if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'
for _n,_s in {'f1':'if !(1..=st.max_fee).contains(&f){','f2':'if f.wrapping_sub(1)>=st.max_fee{','f3':'if f.checked_sub(1).map_or(true,|g|g>=st.max_fee){','f4':'if !(f>0&&f<=st.max_fee){','f5':'if f>st.max_fee||f<1{','f6':'if (f==0)|(f>st.max_fee){'}.items():
    G['F_'+_n]=[(_F338,_s+'return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}')]
def tlx(line0,field,order):
    def f(s):
        L=s.split('\n'); l=L[line0]
        m=_re.search(r'([,{(])'+field+r':(a\.[\w.]+?)\.to_account_info\(\)',l); assert m,(field,line0)
        expr=m.group(2); src=expr+'.as_ref()' if field not in ('coin_creator','pump_creator_vault') else '&'+expr
        L[line0]=l[:m.start()]+m.group(1)+field+':'+_lit(src,order)+l[m.end():]
        return '\n'.join(L)
    return f
_TF=['payer','quote_mint','token_program','system_program','associated_token_program','coin_creator','coin_creator_vault_authority','pump_creator_vault','event_authority']
for _f in _TF:
    for _o in ('KLDORSWE','KDLORSWE','KOLDRSWE','KODLRSWE'):
        G['TX_%s_%s'%(_f,_o)]=[tlx(660,_f,_o)]
for _o in ('KLDORSWE','KDLORSWE','KOLDRSWE','KODLRSWE'):
    G['SX_sharing_config_%s'%_o]=[tlx(748,'sharing_config',_o)]
_EHu=(_EH,'let hopt=hb as u8;let holder=hb;')
_HB='let hb=holder.unwrap_or(false);'
_SH='!a.sharing_config.data_is_empty();let holder_key;'
_STB='let (holder,cashback,target,sharing_update,collect_old,skip)={ let st=CtoState{'
G['q1u']=[(_SH,_SH.replace('let holder_key;',_HB+'let holder_key;')),_EHu]+_VBU
G['q1n']=[(_SH,_SH.replace('let holder_key;',_HB+'let holder_key;')),_EH3]+_VB
G['q2u']=[(_STB,_STB.replace('{ let st=','{ '+_HB+'let st=')),_EHu]+_VBU
G['q2n']=[(_STB,_STB.replace('{ let st=','{ '+_HB+'let st=')),_EH3]+_VB
G['q3u']=[('let mint=a.mint.key();let shared=','let mint=a.mint.key();'+_HB+'let shared='),_EHu]+_VBU
G['q4u']=[(_EH,_HB+'let hopt=hb as u8;let holder=hb;')]+_VBU
G['q4n']=[(_EH,_HB+'let hopt=hb;let holder=hb;')]+_VB
G['q5u']=[('let quote_locked=','let hb=holder.unwrap_or(false);let quote_locked='),_EHu]+_VBU
def reload(k,fld):
    def f(s):
        m=_lits(s)[k]; pre=s[max(0,m.start()-80):m.start()]
        mm=_re.search(r'let x:&AccountInfo= ?(a\.\w+)\.as_ref\(\);$',pre); assert mm,(k,pre)
        base=mm.group(1); body=m.group(1); old='x.'+fld; assert body.count(old)==1,(k,fld)
        nb=body.replace(old,base+'.'+fld)
        return s[:m.start(1)]+nb+s[m.end(1):]
    return f
for _k in (0,1,2,3,4,5,7,9):
    for _f in ('lamports','data','key','owner','rent_epoch','is_signer','is_writable','executable'):
        G['RL%d_%s'%(_k,_f)]=[reload(_k,_f)]
_R=_j.load(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'rev3315.json')))
G['RVW']=[tuple(_R[0]),tuple(_R[1])]
G['RVN']=[tuple(_R[2]),tuple(_R[3]),tuple(_R[4])]
G['RVJ']=[tuple(_R[5]),tuple(_R[6]),tuple(_R[7])]
G['RVT']=[tuple(_R[8])]
G['RVE']=[tuple(_R[9]),('new_creator_fee_bps:a.bonding_curve.creator_fee_bps,','new_creator_fee_bps:nf,')]
G['sw']=[('  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n','  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n')]
# ---- w14a75 additions
_NJ0='   (if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{'
_ENS='crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;'
_TN='crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)'
G['J2']=[(_NJ0,'   if amount>0{'+_ENS+_TN+'?;}Ok(amount)}else{')]
G['J3']=[(_NJ0,'   if amount>0{'+_ENS+_TN+'.map(|()|amount)}else{Ok(0)}}else{')]
G['J4']=[(_NJ0,'   if amount==0{Ok(amount)}else{'+_ENS+_TN+'.map(|()|amount)}}else{')]
G['J5']=[(_NJ0,'   if amount>0{'+_ENS+_TN+'.and(Ok(amount))}else{Ok(amount)}}else{')]
G['J6']=[(_NJ0,'   if amount>0{'+_ENS+_TN+'?;Ok(amount)}else{Ok(amount)}}else{')]
G['cbif']=[('let cashback=!holder&&st.cashback;','let cashback=if holder{false}else{st.cashback};')]
G['B']=G['p3u']+G['tu8']
_VSIG='new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
_VRET='Ok(target)}pub fn execute'
_ECB='let cashback=!holder&&st.cashback;'
_EVAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
_HARM='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
_EARM='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
_VCB=' let cashback=if holder{false}else{st.cashback};'
_RET2=[(_VSIG,_VSIG.replace('Result<Pubkey>','Result<(Pubkey,bool)>')),(_VRET,'Ok((target,cashback))}pub fn execute'),(_ECB,''),(_EVAL,'let (mut target,cashback)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]
G['C1']=_RET2+[(_HARM,_HARM.replace('let target=','let (target,cashback)=').replace('*holder_key}else{','(*holder_key,false)}else{')),(_EARM,_EARM[:-3]+'(t,st.cashback)};'),(_VCB,' ')]
G['C2']=_RET2
G['C3']=_RET2+[(_VCB,' let cashback=!holder&&st.cashback;')]
_296='if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}'
_E296='return Err(error!(PumpError::HolderRewardDisabled));'
G['s1']=[(_296,'if holder&&!(st.holder_reward||st.holder_enabled){'+_E296+'}')]
G['s2']=[(_296,'if !st.holder_reward&&holder&&!st.holder_enabled{'+_E296+'}')]
G['s3']=[(_296,'if holder&&!st.holder_enabled&&!st.holder_reward{'+_E296+'}')]
G['s4']=[(_296,'if !st.holder_enabled&&!st.holder_reward&&holder{'+_E296+'}')]
G['s5']=[(_296,'if holder&&!st.holder_reward{if !st.holder_enabled{'+_E296+'}}')]
G['s6']=[(_296,'if holder&&!st.holder_reward&&st.holder_enabled==false{'+_E296+'}')]
G['s8']=[(_296,'if holder&!st.holder_reward&!st.holder_enabled{'+_E296+'}')]
G['s9']=[(_296,'if !st.holder_reward&&!st.holder_enabled&&holder{'+_E296+'}')]
G['s10']=[(_296,'if holder&&!st.holder_reward&&!st.holder_enabled{'+_E296+'}else{}')]
G['p1']=[(_296,'if !(holder&&!st.holder_reward&&!st.holder_enabled){}else{'+_E296+'}')]
G['p2']=[(_296,'if !holder||st.holder_reward||st.holder_enabled{}else{'+_E296+'}')]
G['p3']=[(_296,'match holder&&!st.holder_reward&&!st.holder_enabled{false=>{},true=>'+_E296+'}')]
G['p4']=[(_296,'if (holder&&!st.holder_reward&&!st.holder_enabled)==false{}else{'+_E296+'}')]
G['p5']=[(_296,'if holder&&!st.holder_reward&&!st.holder_enabled{'+_E296+'}else{}')]
G['t1']=[(_HARM,_HARM.replace('let target=if holder{','let target=match holder{true=>{').replace('*holder_key}else{','*holder_key}false=>{')),(_EARM,_EARM[:-2]+'}};')]
G['t2']=[(_HARM,_HARM.replace('let target=if holder{','let target=if holder==true{'))]
G['t4']=[(_HARM,_HARM.replace('let target=if holder{','let target=if let true=holder{'))]
G['t5']=[(_HARM,_HARM.replace('let target=if holder{','let target=match holder{false=>None,true=>Some(()),}.map_or_else(||{0u8},|()|1u8);let target=if target!=0{'))]
_E298='return Err(error!(PumpError::CtoNewCreatorNotAllowed));'
G['g1']=[(_HARM,'if holder&&new.is_some(){'+_E298+'}let target=if !holder{'),(_EARM,_EARM[:-2]+'}else{*holder_key};')]
G['g2']=[(_HARM,'if holder&&new.is_some(){'+_E298+'}let target=if holder{*holder_key}else{')]
G['g3']=[(_HARM,'if holder{if new.is_some(){'+_E298+'}}let target=if holder{*holder_key}else{')]
G['g4']=[(_HARM,'if holder{if new.is_some(){'+_E298+'}}let target=if !holder{'),(_EARM,_EARM[:-2]+'}else{*holder_key};')]
_H298='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
G['i1']=[(_296,'let target=if holder{if !st.holder_reward&&!st.holder_enabled{'+_E296+'}'),(_H298,'if new.is_some(){'+_E298+'}*holder_key}else{')]
G['i2']=[(_296,'let target=if holder{if st.holder_reward||st.holder_enabled{}else{'+_E296+'}'),(_H298,'if new.is_some(){'+_E298+'}*holder_key}else{')]
G['i3']=[(_296,'let target=if holder{match st.holder_reward||st.holder_enabled{true=>{},false=>'+_E296+'}'),(_H298,'if new.is_some(){'+_E298+'}*holder_key}else{')]
G['i4']=[(_296,'let target=if holder{if !st.holder_enabled&&!st.holder_reward{'+_E296+'}'),(_H298,'if new.is_some(){'+_E298+'}*holder_key}else{')]
def _mt(head):
    return [(_HARM,_HARM.replace('let target=if holder{',head).replace('*holder_key}else{','*holder_key}_=>{')),(_EARM,_EARM[:-2]+'}};')]
G['m1']=_mt('let target=match hopt&1{1=>{')
G['m2']=_mt('let target=match holder as u8{1=>{')
G['m3']=_mt('let target=match hopt{1=>{')
G['m4']=_mt('let target=match hopt&1!=0{true=>{')
