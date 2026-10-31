# w15a01 devolfill genes: w14a138 library (genes_p) + one-instruction validate spellings on the Q3 base
# (Q3 = main 90300f9 + w14a115 devol338st + vol334_back; no read_volatile left). Experiment only.
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_p as _P
G=_P.G
def apply(s,names):
    for n in names:
        for a,b in G[n]:
            if callable(a): s=a(s); continue
            c=s.count(a)
            if c!=1: raise Exception(f'{n}: count {c} for {a[:80]}')
            s=s.replace(a,b)
    return s
E='return Err(error!(PumpError::CreatorFeeBpsOutOfRange));'
F338=f'if f==0||f>st.max_fee{{{E}}}'
G['s_sep']=[(F338,f'if f==0{{{E}}}if f>st.max_fee{{{E}}}')]
G['s_seprev']=[(F338,f'if f>st.max_fee{{{E}}}if f==0{{{E}}}')]
G['s_sepelse']=[(F338,f'if f==0{{{E}}}else if f>st.max_fee{{{E}}}')]
G['s_lt1']=[(F338,f'if f<1||f>st.max_fee{{{E}}}')]
G['s_ge']=[(F338,f'if !(f>=1&&f<=st.max_fee){{{E}}}')]
G['s_match']=[(F338,f'match f{{0=>{{{E}}},f if f>st.max_fee=>{{{E}}},_=>{{}}}}')]
H0='{let holder=hopt==Some(true);'
G['h_unwrap']=[(H0,'{let holder=hopt.unwrap_or(false);')]
G['h_default']=[(H0,'{let holder=hopt.unwrap_or_default();')]
G['h_matches']=[(H0,'{let holder=matches!(hopt,Some(true));')]
G['h_isand']=[(H0,'{let holder=hopt.is_some_and(|h|h);')]
G['h_iflet']=[(H0,'{let holder=if let Some(true)=hopt{true}else{false};')]
G['h_298']=[('if hr&&!(hopt==Some(true)){','if hr&&!holder{')]
G['h_298u']=[('if hr&&!(hopt==Some(true)){','if hr&&!hopt.unwrap_or(false){')]
G['h_298ne']=[('if hr&&!(hopt==Some(true)){','if hr&&hopt!=Some(true){')]
G['h_298m']=[('if hr&&!(hopt==Some(true)){','if hr&&!matches!(hopt,Some(true)){')]
G['h_dis_ord']=[('if holder&&!hr&&!st.holder_enabled{','if holder&&!st.holder_enabled&&!hr{')]
G['h_dis_or']=[('if holder&&!hr&&!st.holder_enabled{','if holder&&!(hr||st.holder_enabled){')]
G['h_dis_st']=[('if holder&&!hr&&!st.holder_enabled{','if holder&&!st.holder_reward&&!st.holder_enabled{')]
NS='if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}'
G['n_ne']=[(NS,'if new!=None{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}')]
G['n_iflet']=[(NS,'if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}')]
G['n_match']=[(NS,'match new{Some(_)=>return Err(error!(PumpError::CtoNewCreatorNotAllowed)),None=>{}}')]
TR='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
G['t_letelse']=[(TR,'let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
G['t_match']=[(TR,'let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};')]
G['t_okor']=[(TR,'let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;')]
G['t_isnone']=[(TR,'if new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}let t=new.unwrap();')]
IC='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}'
G['i_swap']=[(IC,'if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}')]
G['i_ref']=[(IC,'if &t==sharing||&t==holder_key{return Err(error!(PumpError::InvalidCreator));}')]
G['i_sep']=[(IC,'if t==*sharing{return Err(error!(PumpError::InvalidCreator));}if t==*holder_key{return Err(error!(PumpError::InvalidCreator));}')]
G['i_cont']=[(IC,'if [*sharing,*holder_key].contains(&t){return Err(error!(PumpError::InvalidCreator));}')]
G['z_ref']=[('if t==Pubkey::default(){','if t.eq(&Pubkey::default()){')]
G['cb_inl']=[('  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','  if !holder&&st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
G['cb_st']=[('  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','  if st.cashback&&!holder{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
ST='st.fee_configurable=false;}None=>{}}'
G['d_maxf']=[(ST,'st.max_fee=f;}None=>{}}')]
G['d_none']=[(ST,'}None=>{}}')]
G['d_pre']=[('  if !st.fee_configurable{return','  if !st.fee_configurable{return'),(f'{F338}st.fee_configurable=false;',f'st.fee_configurable=false;{F338}')]
G['m_mayeq']=[(' if st.mayhem{return',' if st.mayhem{return')]
# size-knob catalog entries as k_<name>
import json as _j
for _v in _j.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    _e=_v.get('edit') or []
    if _e and all(x.get('old') for x in _e): G['k_'+_v['name']]=[(x['old'],x['new']) for x in _e]
# ---- batch 3: validate parameter passing and fee-arm spellings ----
SIG='fn validate(st:&mut CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
CALL='validate(&mut st,hopt,fee,new,&holder_key,&sk)?'
def _sig(a,b): return [(SIG,SIG.replace(a[0],a[1])),(CALL,CALL.replace(b[0],b[1]))]
G['p_newref']=[(SIG,SIG.replace('new:Option<Pubkey>','new:&Option<Pubkey>')),(CALL,CALL.replace(',new,',',&new,')),
  ('if let Some(t)=new{t}','if let Some(t)=*new{t}')]
G['p_feeref']=[(SIG,SIG.replace('fee:Option<u64>','fee:&Option<u64>')),(CALL,CALL.replace(',fee,',',&fee,')),(' match fee{Some(f)=>{',' match *fee{Some(f)=>{')]
G['p_hoptref']=[(SIG,SIG.replace('hopt:Option<bool>','hopt:&Option<bool>')),(CALL,CALL.replace(',hopt,',',&hopt,')),('{let holder=hopt==Some(true);','{let holder=*hopt==Some(true);'),('if hr&&!(hopt==Some(true)){','if hr&&!(*hopt==Some(true)){')]
G['p_shval']=[(SIG,SIG.replace('sharing:&Pubkey','sharing:Pubkey')),(CALL,CALL.replace('&sk)','sk)')),('if t==*sharing||','if t==sharing||')]
G['p_hkval']=[(SIG,SIG.replace('holder_key:&Pubkey','holder_key:Pubkey')),(CALL,CALL.replace('&holder_key,','holder_key,')),('*holder_key}else{','holder_key}else{'),('||t==*holder_key{','||t==holder_key{')]
G['p_ord']=[(SIG,SIG.replace('fee:Option<u64>,new:Option<Pubkey>','new:Option<Pubkey>,fee:Option<u64>')),(CALL,CALL.replace('fee,new','new,fee'))]
FA=' match fee{Some(f)=>{if st.quote_locked{'
G['f_issome']=[(FA,' if fee.is_some(){let f=fee.unwrap();if st.quote_locked{'),('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}')]
G['f_asref']=[(FA,' if let Some(&f)=fee.as_ref(){if st.quote_locked{'),('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}')]
G['f_for']=[(FA,' for f in fee{if st.quote_locked{'),('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}')]
G['f_nonewild']=[('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}_=>{}}')]
G['f_ref']=[(FA,' match &fee{Some(f)=>{let f=*f;if st.quote_locked{')]
G['hk_clone']=[('*holder_key}else{','holder_key.clone()}else{')]
G['hk_bytes']=[('*holder_key}else{','Pubkey::new_from_array(holder_key.to_bytes())}else{')]
G['t_copy']=[('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};','if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t.clone()};')]
G['ok_ret']=[(' Ok(target)}pub fn execute',' return Ok(target);}pub fn execute')]
G['may_ret']=[(' if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}',' if st.mayhem{Err(error!(PumpError::CtoNotAllowedForMayhemCoin))?;}')]
G['cf_q']=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','  if !st.fee_configurable{Err(error!(PumpError::CreatorFeeNotConfigurable))?;}')]
G['r_q']=[('{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable','{Err(error!(PumpError::CreatorFeeBpsOutOfRange))?;}st.fee_configurable')]
G['ql_q']=[('Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}','Some(f)=>{if st.quote_locked{Err(error!(PumpError::CreatorFeeNotConfigurableForQuote))?;}')]
G['cb_q']=[('  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','  if cashback{Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin))?;}')]
G['req_cf']=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','  require!(st.fee_configurable,PumpError::CreatorFeeNotConfigurable);')]
G['req_r']=[('if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}','require!(f>0&&f<=st.max_fee,PumpError::CreatorFeeBpsOutOfRange);')]
G['req_ql']=[('Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}','Some(f)=>{require!(!st.quote_locked,PumpError::CreatorFeeNotConfigurableForQuote);')]
G['req_cb']=[('  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','  require!(!cashback,PumpError::CreatorFeeNotAllowedForCashbackCoin);')]
G['req_may']=[(' if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}',' require!(!st.mayhem,PumpError::CtoNotAllowedForMayhemCoin);')]
G['req_neq']=[('if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}','require_keys_neq!(t,Pubkey::default(),PumpError::CreatorShouldNotBeZero);')]
# ---- batch 4: fee-arm return forms on D4 (= Q3 + d_none: no placeholder, no store). Use as d_none+<gene> ----
_OK='CreatorFeeBpsOutOfRange));}}None=>{}}\n Ok(target)}pub fn execute'
G['r_some']=[(_OK,'CreatorFeeBpsOutOfRange));}return Ok(target);}None=>{}}\n Ok(target)}pub fn execute')]
G['r_none']=[(_OK,'CreatorFeeBpsOutOfRange));}}None=>return Ok(target)}\n Ok(target)}pub fn execute')]
G['r_expr']=[(_OK,'CreatorFeeBpsOutOfRange));}Ok(target)}None=>Ok(target)}\n }pub fn execute')]
G['r_expr2']=[(_OK,'CreatorFeeBpsOutOfRange));}}None=>{}}\n return Ok(target);}pub fn execute')]
G['r_letelse']=[(' match fee{Some(f)=>{if st.quote_locked{',' let Some(f)=fee else{return Ok(target);};if st.quote_locked{'),(_OK,'CreatorFeeBpsOutOfRange));}\n Ok(target)}pub fn execute')]
G['r_letmatch']=[(' match fee{Some(f)=>{if st.quote_locked{',' let f=match fee{Some(f)=>f,None=>return Ok(target)};if st.quote_locked{'),(_OK,'CreatorFeeBpsOutOfRange));}\n Ok(target)}pub fn execute')]
G['r_ifnone']=[(' match fee{Some(f)=>{if st.quote_locked{',' if fee.is_none(){return Ok(target);}let f=fee.unwrap();if st.quote_locked{'),(_OK,'CreatorFeeBpsOutOfRange));}\n Ok(target)}pub fn execute')]
G['r_nonefirst']=[(' match fee{Some(f)=>{if st.quote_locked{',' match fee{None=>Ok(target),Some(f)=>{if st.quote_locked{'),(_OK,'CreatorFeeBpsOutOfRange));}Ok(target)}}\n }pub fn execute')]
G['r_okq']=[(_OK,'CreatorFeeBpsOutOfRange));}}None=>{}}\n Ok::<_,anchor_lang::error::Error>(target)}pub fn execute')]
# ---- batch 5: placement of locals and comparison spellings in validate (on Q3) ----
G['l_holder284']=[('{let holder=hopt==Some(true);\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}','{\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}let holder=hopt==Some(true);')]
G['l_cbarm']=[(' let cashback=if holder{false}else{st.cashback};',''),(' match fee{Some(f)=>{if st.quote_locked{',' match fee{Some(f)=>{let cashback=if holder{false}else{st.cashback};if st.quote_locked{')]
G['l_cbarm2']=[(' let cashback=if holder{false}else{st.cashback};',''),('  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','  let cashback=if holder{false}else{st.cashback};if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
G['l_cbtop']=[(' let cashback=if holder{false}else{st.cashback};',''),('{let holder=hopt==Some(true);','{let holder=hopt==Some(true);let cashback=if holder{false}else{st.cashback};')]
G['l_hrtop']=[(' let hr=st.holder_reward;if hr&&',' if hr&&'),('{let holder=hopt==Some(true);','{let holder=hopt==Some(true);let hr=st.holder_reward;')]
G['n_notnone']=[('if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}','if !new.is_none(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}')]
G['hk_owned']=[('*holder_key}else{','holder_key.to_owned()}else{')]
G['i_eq']=[('if t==*sharing||t==*holder_key{','if t.eq(sharing)||t.eq(holder_key){')]
G['i_rev']=[('if t==*sharing||t==*holder_key{','if *sharing==t||*holder_key==t{')]
G['z_rev']=[('if t==Pubkey::default(){','if Pubkey::default()==t{')]
G['f_mxlt']=[('if f==0||f>st.max_fee{','if f==0||st.max_fee<f{')]
G['ql_eqf']=[('Some(f)=>{if st.quote_locked{','Some(f)=>{if st.quote_locked!=false{')]
G['hold_tern']=[(' let target=if holder{if new.is_some()',' let target=if holder==true{if new.is_some()')]
G['hold_not']=[('if holder&&!hr&&!st.holder_enabled{','if holder&&!hr&&st.holder_enabled==false{')]
# ---- batch 6: validated-fee re-wrap (original's fee-OK edge carries a phi constant mov r7,1). Use as d_none+<gene> ----
_SIGR='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder'
_OK6='CreatorFeeBpsOutOfRange));}}None=>{}}\n Ok(target)}pub fn execute'
_FA6=' match fee{Some(f)=>{if st.quote_locked{'
_BLK=('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fee)={')
_BLE=('(holder,cashback,target,sharing_update,collect_old,skip)};','(holder,cashback,target,sharing_update,collect_old,skip,fee)};')
_CL=('let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fee)=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;')
G['w_tup']=[(_SIGR,'holder_key:&Pubkey,sharing:&Pubkey)->Result<(Pubkey,Option<u64>)>{let holder'),(_FA6,' let fee=match fee{Some(f)=>{if st.quote_locked{'),
  (_OK6,'CreatorFeeBpsOutOfRange));}Some(f)}None=>None};\n Ok((target,fee))}pub fn execute'),_BLK,_BLE,_CL]
G['w_tupb']=[(_SIGR,'holder_key:&Pubkey,sharing:&Pubkey)->Result<(Pubkey,bool)>{let holder'),(_FA6,' let fs=match fee{Some(f)=>{if st.quote_locked{'),
  (_OK6,'CreatorFeeBpsOutOfRange));}true}None=>false};\n Ok((target,fs))}pub fn execute'),
  ('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fs)={'),
  ('(holder,cashback,target,sharing_update,collect_old,skip)};','(holder,cashback,target,sharing_update,collect_old,skip,fs)};'),
  ('let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fs)=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;'),
  ('if let Some(f)=fee{curve.creator_fee_bps=f;}','if fs{curve.creator_fee_bps=fee.unwrap();}')]
# fee as Option returned only (target via out tuple order swapped)
G['w_tup2']=[(_SIGR,'holder_key:&Pubkey,sharing:&Pubkey)->Result<(Option<u64>,Pubkey)>{let holder'),(_FA6,' let fee=match fee{Some(f)=>{if st.quote_locked{'),
  (_OK6,'CreatorFeeBpsOutOfRange));}Some(f)}None=>None};\n Ok((fee,target))}pub fn execute'),_BLK,_BLE,
  ('let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;','let (fee,mut target)=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;')]
# ---- batch 7: CtoState literal field order (move one field first/last) and validate call-site spellings (on Q3) ----
_LIT='creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable'
_F=_LIT.split(',')
for _i,_x in enumerate(_F):
    _n=_x.split(':')[0]
    if _i!=0: G['lf_'+_n]=[('CtoState{'+_LIT+'}','CtoState{'+','.join([_x]+_F[:_i]+_F[_i+1:])+'}')]
    if _i!=len(_F)-1: G['ll_'+_n]=[('CtoState{'+_LIT+'}','CtoState{'+','.join(_F[:_i]+_F[_i+1:]+[_x])+'}')]
_C='validate(&mut st,hopt,fee,new,&holder_key,&sk)?'
G['c_sk']=[(_C,'validate(&mut st,hopt,fee,new,&holder_key,&a.sharing_config.key())?')]
G['c_hk']=[(_C,'validate(&mut st,hopt,fee,new,&hk.0,&sk)?')]
G['c_new']=[(_C,'validate(&mut st,hopt,fee,args.0,&holder_key,&sk)?')]
G['c_hold']=[(_C,'validate(&mut st,holder,fee,new,&holder_key,&sk)?')]
# ---- batch 8: on top of lf_fee_configurable (fee_configurable first in the CtoState literal) ----
_L1='CtoState{fee_configurable:a.global.creator_fee_configurable,'+','.join(_F[:-1])+'}'
_G1=_L1[len('CtoState{'):-1].split(',')
for _i,_x in enumerate(_G1):
    if _i<=1: continue
    _n=_x.split(':')[0]
    G['l2s_'+_n]=[('CtoState{'+_LIT+'}','CtoState{'+','.join([_G1[0],_x]+_G1[1:_i]+_G1[_i+1:])+'}')]
for _i,_x in enumerate(_G1):
    if _i==0 or _i==len(_G1)-1: continue
    _n=_x.split(':')[0]
    G['l2l_'+_n]=[('CtoState{'+_LIT+'}','CtoState{'+','.join(_G1[:_i]+_G1[_i+1:]+[_x])+'}')]
