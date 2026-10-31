import json,os
G={}
_K=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']
for k in _K:
    if k.get('edit'): G['k_'+k['name']]=[(e['old'],e['new']) for e in k['edit']]
_V1="  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{"
_V2="return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}"
_FS=" match fee{Some(f)=>{if st.quote_locked{"
G['fNf']=[(_FS," match fee{None=>{},Some(f)=>{if st.quote_locked{"),("as *const u8)};}None=>{}}","as *const u8)};}}")]
G['dv1']=[(_V1,"  if !st.fee_configurable{")]
G['dv2']=[(_V2,"return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}")]
G['cbi']=[(" let cashback=if holder{false}else{st.cashback};"," let cashback=!holder&&st.cashback;")]
G['cbs']=[(" let cashback=if holder{false}else{st.cashback};"," "),("  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}","  if !holder&&st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}")]
G['cbh']=[(" let cashback=if holder{false}else{st.cashback};"," "),("  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}","  if st.cashback&&!holder{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}")]
G['ifl']=[(_FS," if let Some(f)=fee{if st.quote_locked{"),("as *const u8)};}None=>{}}","as *const u8)};}")]
G['le306']=[("  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};","  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};")]
G['mt306']=[("  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};","  let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};")]
G['ok306']=[("  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};","  let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;")]
_ICd="fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}"
G['icv']=[(_ICd,"fn invalid_creator(t:Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{t==*sharing||t==*holder_key}"),("if invalid_creator(&t,sharing,holder_key){","if invalid_creator(t,sharing,holder_key){")]
G['ica']=[(_ICd,"fn invalid_creator(t:&Pubkey,keys:[&Pubkey;2])->bool{keys.contains(&t)}"),("if invalid_creator(&t,sharing,holder_key){","if invalid_creator(&t,[sharing,holder_key]){")]
G['icn']=[(_ICd,"fn valid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t!=*sharing&&*t!=*holder_key}"),("if invalid_creator(&t,sharing,holder_key){","if !valid_creator(&t,sharing,holder_key){")]
_T306="  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
G['tnz']=[(_T306,"  if new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}let t=new.unwrap();")]
G['tby']=[(_T306,"  let t=if let Some(t)=new{Pubkey::new_from_array(t.to_bytes())}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")]
G['tref']=[(_T306,"  let t=if let Some(t)=&new{*t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")]
G['tas']=[(_T306,"  let t=if let Some(t)=new.as_ref(){*t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")]
G['tcp']=[(_T306,"  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};let t=t.clone();")]
G['tbx']=[(_T306,"  let t:Pubkey=if let Some(t)=new{t.to_bytes().into()}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")]
# per-arm cashback returned from validate (original computes cashback per arm as a phi of constants/st.cashback)
_VS="holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"
_TH=" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
_TE="return Err(error!(PumpError::InvalidCreator));}t};"
_CB=" let cashback=if holder{false}else{st.cashback};"
_EX="let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
G['pcb']=[(_VS,"holder_key:&Pubkey,sharing:&Pubkey)->Result<(Pubkey,bool)>{let holder=hopt==Some(true);"),
 (_TH," let (target,cashback)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,false)}else{"),
 (_TE,"return Err(error!(PumpError::InvalidCreator));}(t,st.cashback)};"),(_CB," "),
 ("None=>{}}\n Ok(target)}pub fn execute","None=>{}}\n Ok((target,cashback))}pub fn execute"),
 (_EX,"let args=&(new,);let sk=a.sharing_config.key();let (mut target,cashback)=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pcb2']=[(_VS,"holder_key:&Pubkey,sharing:&Pubkey)->Result<(Pubkey,bool)>{let holder=hopt==Some(true);"),
 ("None=>{}}\n Ok(target)}pub fn execute","None=>{}}\n Ok((target,cashback))}pub fn execute"),
 (_EX,"let args=&(new,);let sk=a.sharing_config.key();let (mut target,cashback)=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['pcb3']=[(_VS,"holder_key:&Pubkey,sharing:&Pubkey)->Result<(bool,Pubkey)>{let holder=hopt==Some(true);"),
 (_TH," let (cashback,target)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(false,*holder_key)}else{"),
 (_TE,"return Err(error!(PumpError::InvalidCreator));}(st.cashback,t)};"),(_CB," "),
 ("None=>{}}\n Ok(target)}pub fn execute","None=>{}}\n Ok((cashback,target))}pub fn execute"),
 (_EX,"let args=&(new,);let sk=a.sharing_config.key();let (cashback,mut target)=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
_RG="  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}"
G['fsp']=[(_RG,"  if f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}if f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}")]
G['fspr']=[(_RG,"  if f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}if f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}")]
G['frv']=[(_RG,"  if f>st.max_fee||f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}")]
G['frn']=[(_RG,"  if !(1..=st.max_fee).contains(&f){return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}")]
G['cav']=[(_EX,"let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let cashback=!holder&&st.cashback;")]
_S312="  if invalid_creator(&t,sharing,holder_key){return Err(error!(PumpError::InvalidCreator));}t};"
_VC=("fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}","fn valid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t!=*sharing&&*t!=*holder_key}")
G['p_ie']=[(_S312,"  if !invalid_creator(&t,sharing,holder_key){t}else{return Err(error!(PumpError::InvalidCreator));}};")]
G['p_vc']=[_VC,(_S312,"  if valid_creator(&t,sharing,holder_key){t}else{return Err(error!(PumpError::InvalidCreator));}};")]
G['p_mt']=[(_S312,"  match invalid_creator(&t,sharing,holder_key){true=>return Err(error!(PumpError::InvalidCreator)),false=>t}};")]
G['p_mf']=[(_S312,"  match invalid_creator(&t,sharing,holder_key){false=>t,true=>return Err(error!(PumpError::InvalidCreator))}};")]
G['p_le']=[(_S312,"  if invalid_creator(&t,sharing,holder_key){return Err(error!(PumpError::InvalidCreator))}else{t}};")]
G['p_bd']=[(_S312,"  let bad=invalid_creator(&t,sharing,holder_key);if bad{return Err(error!(PumpError::InvalidCreator));}t};")]
G['p_vr']=[_VC,(_S312,"  if !valid_creator(&t,sharing,holder_key){return Err(error!(PumpError::InvalidCreator));}t};")]
G['p_rq']=[(_S312,"  require!(!invalid_creator(&t,sharing,holder_key),PumpError::InvalidCreator);t};")]
G['vcb']=[("fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,cashback:bool)->Result<Pubkey>{"),
 (_CB," "),("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,cashback)?;")]
G['vcb2']=[("fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","fn validate(cashback:bool,st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),
 (_CB," "),("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(cashback,&st,hopt,fee,new,&holder_key,&sk)?;")]
G['noargs']=[("let args=&(new,);",""),("sharing_update=Some(args.0);","sharing_update=Some(new);")]
G['argsv']=[("let args=&(new,);","let args=(new,);")]
G['argsaft']=[("let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let args=&(new,);")]
G['newcp']=[("let args=&(new,);","let args=&(new,);let new=args.0;")]
_VC1="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
G['g1']=[(_VC1,"let creator=st.creator;"+_VC1),("target=a.bonding_curve.creator;","target=creator;")]
G['g3a']=[("{ let st=CtoState{","{ let creator=a.bonding_curve.creator;let st=CtoState{"),("target=a.bonding_curve.creator;","target=creator;")]
G['g3b']=[("{ let st=CtoState{","{ let creator=st_creator(a);let st=CtoState{")]
G['g0']=[("target=a.bonding_curve.creator;","target=st.creator;")]
G['f7']=[(_VC1,_VC1+"let creator=a.bonding_curve.creator;"),("target=a.bonding_curve.creator;","target=creator;")]
_VSIG="new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
_T312E="return Err(error!(PumpError::InvalidCreator));}t};"
G['ov15']=[(_VSIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<Pubkey>{"),(_T312E,"return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
 (_VC1,"let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;"),("target=a.bonding_curve.creator;","")]
G['ove15']=[(_VSIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,ov:Option<Pubkey>)->Result<Pubkey>{"),(_T312E,"return Err(error!(PumpError::InvalidCreator));}ov.unwrap_or(t)};"),
 (_VC1,"let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared.then_some(st.creator))?;"),("target=a.bonding_curve.creator;","")]
G['ove15b']=[(_VSIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,ov:Option<Pubkey>)->Result<Pubkey>{"),(_T312E,"return Err(error!(PumpError::InvalidCreator));}match ov{Some(c)=>c,None=>t}};"),
 (_VC1,"let ov=if shared{Some(st.creator)}else{None};let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,ov)?;"),("target=a.bonding_curve.creator;","")]
