G={}
_FV="fn validate(st:&CtoState,"
_312="  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
_307="  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}"
def H(defs): return [("\n\n"+_FV,"\n"+defs+"\n"+_FV)]
# helper-bool forms (branch on an un-inlined call is 50/50 in validate's pre-inline BFI)
G['h312']=H("fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}")+[(_312,"  if invalid_creator(&t,sharing,holder_key){return Err(error!(PumpError::InvalidCreator));}t};")]
G['h307']=H("fn is_zero(t:&Pubkey)->bool{*t==Pubkey::default()}")+[(_307,"  if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}")]
G['h307_312']=H("fn is_zero(t:&Pubkey)->bool{*t==Pubkey::default()}fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}")+[(_312,"  if invalid_creator(&t,sharing,holder_key){return Err(error!(PumpError::InvalidCreator));}t};"),(_307,"  if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}")]
# bound bool before the 307 test
G['b312']=[(_307,"  let bad=t==*sharing||t==*holder_key;if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}"),(_312,"  if bad{return Err(error!(PumpError::InvalidCreator));}t};")]
G['bor312']=[(_312,"  if (t==*sharing)|(t==*holder_key){return Err(error!(PumpError::InvalidCreator));}t};")]
G['bor312r']=[(_312,"  if (t==*holder_key)|(t==*sharing){return Err(error!(PumpError::InvalidCreator));}t};")]
_IZ="fn is_zero(t:&Pubkey)->bool{*t==Pubkey::default()}"
_H307=(_307,"  if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}")
_C312=(_312,"  if invalid_creator(&t,sharing,holder_key){return Err(error!(PumpError::InvalidCreator));}t};")
G['z_bor']=H(_IZ)+[_H307]+G['bor312']
G['z_borr']=H(_IZ)+[_H307]+G['bor312r']
G['hb312']=H(_IZ+"fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{(*t==*sharing)|(*t==*holder_key)}")+[_H307,_C312]
G['h307_312r']=H(_IZ+"fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*holder_key||*t==*sharing}")+[_H307,_C312]
# T: the 312-only outline trigger as substring edits (composable after other genes)
G['T']=H(_IZ+"fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}")+[
 ("if t==*sharing||t==*holder_key{","if invalid_creator(&t,sharing,holder_key){"),
 ("if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)","if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero)")]
import mine125
for k in ('c_vb','c_vbu'): G[k]=mine125.G[k]
G['nop']=[]
G['m0']=[('fn validate(','fn validate(')]
_IC="fn invalid_creator(t:&Pubkey,sharing:&Pubkey,holder_key:&Pubkey)->bool{*t==*sharing||*t==*holder_key}"
_I312=("if t==*sharing||t==*holder_key{","if invalid_creator(&t,sharing,holder_key){")
_Z307="if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)"
# T2: 307 via a two-ref key-equality helper; the default temp stays in validate
G['T2']=H("fn same_key(a:&Pubkey,b:&Pubkey)->bool{*a==*b}"+_IC)+[_I312,(_Z307,"if same_key(&t,&Pubkey::default()){return Err(error!(PumpError::CreatorShouldNotBeZero)")]
G['T5']=H("fn is_zero(t:&Pubkey)->bool{t==&Pubkey::default()}"+_IC)+[_I312,(_Z307,"if is_zero(&t){return Err(error!(PumpError::CreatorShouldNotBeZero)")]
