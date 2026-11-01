# w16a06 genes: exact single-occurrence (old,new) replacements in admin_cto.rs (line count kept)
G={}
_FV="fn validate(st:&CtoState,"
def H(defs): return [("\n\n"+_FV,"\n"+defs+"\n"+_FV)]
_IZ="fn is_zero(t:&Pubkey)->bool{*t==Pubkey::default()}"
_IC="fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}"
# T (w14a141 trigger, w15a02): 307 via is_zero, 312 via invalid_creator -> outlines 312 to_string
G['T']=H(_IZ+_IC)+[
 ("if t==*sharing||t==*holder_key{","if invalid_creator(&t,sharing,holder_key){"),
 ("if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)","if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero)")]
_V1="  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{"
G['dv1']=[(_V1,"  if !st.fee_configurable{")]
G['le306']=[("  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};","  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};")]
# v01 (w15a11): 312 compares holder_key first
G['v01']=[("if t==*sharing||t==*holder_key{","if t==*holder_key||t==*sharing{")]
G['Tv01']=H(_IZ+"fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*holder_key||*t==*sharing}")+[
 ("if t==*sharing||t==*holder_key{","if invalid_creator(&t,sharing,holder_key){"),
 ("if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)","if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero)")]
G['nop']=[]

_P289="if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
# h289 (w14a104 one-holder-test; w15a25 T289n/p289n): 289 tests holder itself -> 307/312 cold at V, original outline pattern
G['h289']=[(_P289,"if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")]

# 306 BPI spellings (angle step 4 candidates), each a single-line replacement of line 306
_T306="  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
G['s306mi']=[(_T306,"  let t=match new.is_some() as i32{1=>new.unwrap_or_default(),_=>return Err(error!(PumpError::CtoNewCreatorRequired))};")]
G['s306mz']=[(_T306,"  let t=match new.is_none() as i32{0=>new.unwrap_or_default(),_=>return Err(error!(PumpError::CtoNewCreatorRequired))};")]
G['s306in']=[(_T306,"  let t=if new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}else{new.unwrap_or_default()};")]
G['s306mu']=[(_T306,"  let t=match new.map(|t|t.to_bytes()){Some(b)=>Pubkey::new_from_array(b),None=>return Err(error!(PumpError::CtoNewCreatorRequired))};")]
