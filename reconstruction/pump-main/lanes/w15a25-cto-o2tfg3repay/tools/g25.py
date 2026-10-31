# w15a25 genes: exact single-occurrence (old,new) replacements in admin_cto.rs (line count kept)
G={}
L296=" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
G['h296in']=[(L296," let target=if holder{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n  if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
P289="if st.holder_reward&&!(hopt==Some(true)){"
G['p289m']=[(P289,"if st.holder_reward&&!matches!(hopt,Some(true)){")]
G['p289u']=[(P289,"if st.holder_reward&&!hopt.unwrap_or(false){")]
G['p289h']=[(P289,"if st.holder_reward&&!holder{")]
G['p289ne']=[(P289,"if st.holder_reward&&hopt!=Some(true){")]
G['p289il']=[(P289,"if st.holder_reward&&!(if let Some(true)=hopt{true}else{false}){")]
E289="{return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
E296="{return Err(error!(PumpError::HolderRewardDisabled));}"
E298="{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}"
E306="else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
E312="{return Err(error!(PumpError::InvalidCreator));}"
OLD_A=(" if st.holder_reward&&!(hopt==Some(true))"+E289+"\n\n\n\n\n\n\n"
 " if holder&&!st.holder_reward&&!st.holder_enabled"+E296+"\n\n"
 " let target=if holder{if new.is_some()"+E298+"*holder_key}else{\n")
NB="\n\n\n\n\n\n\n"
def b3(attr):
    return [(OLD_A," let target=if holder{holder_target(st,new,holder_key)?}else{if st.holder_reward"+E289+NB+
      " "+attr+"fn holder_target(st:&CtoState,new:Option<Pubkey>,holder_key:&Pubkey)->Result<Pubkey>{if !st.holder_reward&&!st.holder_enabled"+E296+"\n\n"
      " if new.is_some()"+E298+"Ok(*holder_key)}\n")]
G['B3i']=b3('#[inline] ')
G['B3a']=b3('#[inline(always)] ')
OLD_N=("  let t=if let Some(t)=new{t}"+E306+"\n")
OLD_N2=("  if t==*sharing||t==*holder_key"+E312+"t};\n")
def b4(attr):
    return [(OLD_A," let target=if !holder{if st.holder_reward"+E289+"new_target(new,holder_key,sharing)?}else{"+NB+
      "  if !st.holder_reward&&!st.holder_enabled"+E296+"\n\n"
      "  if new.is_some()"+E298+"*holder_key};\n"),
      (OLD_N," "+attr+"fn new_target(new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let t=if let Some(t)=new{t}"+E306+"\n"),
      (OLD_N2,"  if t==*sharing||t==*holder_key"+E312+"Ok(t)}\n")]
G['B4i']=b4('#[inline] ')
G['B4a']=b4('#[inline(always)] ')
O296=" if holder&&!st.holder_reward&&!st.holder_enabled"+E296
G['h296s']=[(O296," if holder{if !st.holder_reward&&!st.holder_enabled"+E296+"}")]
G['h296o']=[(O296," if holder&&!(st.holder_reward||st.holder_enabled)"+E296)]
G['h296so']=[(O296," if holder{if !(st.holder_reward||st.holder_enabled)"+E296+"}")]
G['v01']=[('if t==*sharing||t==*holder_key{','if t==*holder_key||t==*sharing{')]
_SIG='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder'
_CALL='validate(&st,hopt,fee,new,&holder_key,&sk)'
_RV='read_volatile(holder_key as *const Pubkey as *const u8)'
G['b01x']=[(_SIG,'holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder'),(_CALL,'validate(&st,hopt,fee,new,holder_key,&sk)'),
  ('*holder_key};','holder_key};'),('new_target(new,holder_key,sharing)','new_target(new,&holder_key,sharing)'),
  ('unsafe{core::ptr::'+_RV+'};if !st','unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st'),
  (_RV+'};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
def k(arm296,attr='#[inline(always)] '):
    l296=(" let target=if holder{if !st.holder_reward&&!st.holder_enabled"+E296+"\n\n  if new.is_some()"+E298+"*holder_key}else{immutable(st)?;\n") if arm296 else \
         (" if holder&&!st.holder_reward&&!st.holder_enabled"+E296+"\n\n let target=if holder{if new.is_some()"+E298+"*holder_key}else{immutable(st)?;\n")
    return [(OLD_A," "+attr+"fn immutable(st:&CtoState)->Result<()>{if st.holder_reward"+E289+"Ok(())}"+NB+l296)]
G['K1']=k(True); G['K2']=k(False)
# ---- wave-16 continuation: O-repay grid pieces on main's form (w15a11 b01/b02, w15a10 Fa/Fb)
_SIGm='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>'
_CALLm='validate(&st,hopt,fee,new,&holder_key,&sk)'
_RVm='read_volatile(holder_key as *const Pubkey as *const u8)'
def _hk(call_new='validate(&st,hopt,fee,new,holder_key,&sk)',swap=False):
    e=[(_SIGm,'holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>'),(_CALLm,call_new),('*holder_key}else{','holder_key}else{'),
       ('unsafe{core::ptr::'+_RVm+'};if !st','unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st'),
       (_RVm+'};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
    e.append(('if t==*sharing||t==*holder_key{','if t==holder_key||t==*sharing{') if swap else ('t==*holder_key{','t==holder_key{'))
    return e
G['b01m']=_hk()
G['b02m']=_hk(swap=True)
G['Fa']=[('fee,new,&holder_key','fee,args.0,&holder_key')]
G['b01Fa']=_hk('validate(&st,hopt,fee,args.0,holder_key,&sk)')
G['b02Fa']=_hk('validate(&st,hopt,fee,args.0,holder_key,&sk)',swap=True)
_ST='let st=CtoState{'; _ARGS='let args=&(new,);'; _SA='sharing_update=Some(args.0);'
G['Fb0']=[(_ARGS,''),(_SA,'sharing_update=Some(nc);'),('{ let creator=a.bonding_curve.creator;let st=CtoState{','{ let creator=a.bonding_curve.creator;let nc=new;let st=CtoState{')]
# ---- wave-16 trigger forms (289 holder re-test spellings) for the fast V oracle
_P289="if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
G['p289n']=[(_P289,"if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")]
G['p289e']=[(_P289,"if st.holder_reward&&holder==false{return Err(error!(PumpError::HolderRewardCreatorImmutable));}")]
G['p289ie']=[(_P289,"if st.holder_reward{if holder{}else{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")]
# holder-flag forms combined with the V-threading trigger p289n (and-1 basin probes)
G['vuo']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=hopt.unwrap_or(false);')]
G['vmt']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=matches!(hopt,Some(true));')]
G['euo']=[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=hopt.unwrap_or(false);')]
G['emt']=[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=matches!(hopt,Some(true));')]
# 298-site spellings on top of the p289n trigger (target: the extra 32 B _45.sroa error-temp alloca of the 298 site)
_H298="if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
G['s298l']=[(_H298,"if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
G['s298n']=[(_H298,"if new!=None{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{")]
G['s298r']=[(_H298,"require!(new.is_none(),PumpError::CtoNewCreatorNotAllowed);*holder_key}else{")]
# sharing payload straight from new (the args=(new,) copy is what survives as %_45.sroa.5 under the trigger)
G['sn']=[('sharing_update=Some(args.0);','sharing_update=Some(new);')]
G['sna']=[('sharing_update=Some(args.0);','sharing_update=Some(new);'),('let args=&(new,);','')]
G['sac']=[('let args=&(new,);','let args=(new,);')]
# split on a fresh eq (no early threading of the split), with 289 on holder (p289h): extra 50/50 on every path into the arms
G['v27']=[('let target=if holder{if new.is_some(){','let target=if hopt==Some(true){if new.is_some(){')]
# error-macro spelling of 312, and w13a17's multi-way match (Some case with sibling guard arms)
_L312="  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
G['z312r']=[(_L312,"  require!(t!=*sharing&&t!=*holder_key,PumpError::InvalidCreator);t};")]
_L298=" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
_L306="  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
G['zmw']=[(_L298," let target=match new{Some(_) if holder=>{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}None if holder=>*holder_key,"),
          (_L306,"  None=>{return Err(error!(PumpError::CtoNewCreatorRequired));}Some(t)=>{"),
          (_L312,"  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t}};")]
# w14a07 cold306 f2 port (pricing probe only: the has flag is redundant with new's tag): RAR + has:bool + if let (true,Some(t))
G['rar']=[('let args=&(new,);',''),('let st=CtoState{','let args=&(new,);let st=CtoState{')]
G['f2has']=[('new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>','new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>'),
  ('validate(&st,hopt,fee,new,&holder_key,&sk)','validate(&st,hopt,fee,new,args.0.is_some(),&holder_key,&sk)'),
  ('  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};','  let t=if let (true,Some(t))=(has,new){t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
