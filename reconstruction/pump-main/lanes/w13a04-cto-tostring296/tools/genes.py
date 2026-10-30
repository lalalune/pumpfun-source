E={}
E['Z']=[("fn validate(st:&CtoState,holder:bool,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","fn validate(st:&CtoState,holder:bool,fee:Option<u64>,new:&mut Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
 (" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n let target=if holder{if new"," let target=if holder{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n  if new"),
 ("return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{","return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}else{"),
 ("let Some(t)=new else{","let Some(t)=new.take() else{"),
 ("if t==*holder_key||t==*sharing{","if t==holder_key||t==sharing{"),
 ("fee:Option<u64>,new:Option<Pubkey>)->Result<()>{","fee:Option<u64>,mut new:Option<Pubkey>)->Result<()>{"),
 ("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;","let su=new;let mut target=validate(&st,holder,fee,&mut new,holder_key,a.sharing_config.key())?;"),
 ("target=st.creator;(Some(new),false,true)}","target=st.creator;(Some(su),false,true)}")]
E['OV']=[("holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{","holder_key:Pubkey,sharing:Pubkey,shared:bool)->Result<Pubkey>{"),
 ("if t==holder_key||t==sharing{return Err(error!(PumpError::InvalidCreator));}t};","if t==holder_key||t==sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
 ("a.sharing_config.key())?;","a.sharing_config.key(),shared)?;"),
 ("else{target=st.creator;(Some(su),false,true)}","else{(Some(su),false,true)}"),
 ("let mut target=validate(","let target=validate(")]
E['T298']=[("  if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}","  if new.take().is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}")]
E['NS']=[("swept=(!skip).then(","swept=(shared&&holder).then(")]
E['CB7']=[("if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)","if !holder&&t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)")]
E['CB12']=[("if t==*holder_key||t==*sharing{","if !holder&&(t==*holder_key||t==*sharing){")]
E['IN296']=[(" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n let target=if holder{if new"," let target=if holder{if !st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n\n  if new")]
E['EL296']=[(" if st.holder_reward&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}\n"," if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}\n"),
  (" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n"," else if holder&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n")]
E['BYVAL']=[("new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
 ("return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{","return Err(error!(PumpError::CtoNewCreatorNotAllowed));}holder_key}else{"),
 ("if t==*holder_key||t==*sharing{","if t==holder_key||t==sharing{"),
 ("validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?","validate(&st,holder,fee,new,holder_key,a.sharing_config.key())?")]
E['TAKE306']=[("fee:Option<u64>,new:Option<Pubkey>,holder_key","fee:Option<u64>,mut new:Option<Pubkey>,holder_key"),("let Some(t)=new else{","let Some(t)=new.take() else{")]
E['SU']=[("let mut target=validate(&st,holder,fee,new,","let su=new;let mut target=validate(&st,holder,fee,new,"),("target=st.creator;(Some(new),false,true)}","target=st.creator;(Some(su),false,true)}")]
E['T298M']=[("  if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}","  if new.take().is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}")]
E['OVM']=[("sharing:&Pubkey)->Result<Pubkey>{","sharing:&Pubkey,shared:bool)->Result<Pubkey>{"),
 ("if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};","if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
 ("&a.sharing_config.key())?;","&a.sharing_config.key(),shared)?;"),
 ("else{target=st.creator;(Some(new),false,true)}","else{(Some(new),false,true)}"),
 ("let mut target=validate(","let target=validate(")]
E['OVMK']=E['OVM'][:3]
E['T298E']=[(" let target=if holder{if new.is_some(){"," let target=if holder{if new.take().is_some(){")]
E['MUTSU']=[("fee:Option<u64>,new:Option<Pubkey>,holder_key","fee:Option<u64>,new:&mut Option<Pubkey>,holder_key"),
 ("let Some(t)=new else{","let Some(t)=new.take() else{"),
 ("fee:Option<u64>,new:Option<Pubkey>)->Result<()>{","fee:Option<u64>,mut new:Option<Pubkey>)->Result<()>{"),
 ("let mut target=validate(&st,holder,fee,new,","let su=new;let mut target=validate(&st,holder,fee,&mut new,"),
 ("(Some(new),false,true)}","(Some(su),false,true)}")]
E['HM']=[("fn validate(st:&CtoState,holder:bool,fee:Option<u64>,","fn validate(st:&CtoState,holder:bool,hopt:Option<bool>,fee:Option<u64>,"),
 ("let holder=holder==Some(true);","let hopt=holder;let holder=hopt==Some(true);"),
 ("validate(&st,holder,fee,","validate(&st,holder,hopt,fee,"),
 (" if holder&&!st.holder_reward&&!st.holder_enabled{"," if matches!(hopt,Some(true))&&!st.holder_reward&&!st.holder_enabled{"),
 (" let target=if holder{if new"," let target=if matches!(hopt,Some(true)){if new"),
 (" let cashback=if holder{false}else{st.cashback};"," let cashback=if matches!(hopt,Some(true)){false}else{st.cashback};")]
E['CBA']=[(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," let (target,cashback)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,false)}else{"),
 ("if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};","if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}(t,st.cashback)};"),
 (" let cashback=if holder{false}else{st.cashback};","")]
E['CBAO']=[(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," let (target,cashback)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,false)}else{"),
 ("if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};","if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}(if shared{st.creator}else{t},st.cashback)};"),
 (" let cashback=if holder{false}else{st.cashback};","")]
E['CBR']=[(")->Result<Pubkey>{",")->Result<(Pubkey,bool)>{"),
 (" Ok(target)}pub fn execute"," Ok((target,cashback))}pub fn execute"),
 ("let cashback=!holder&&st.cashback;let mut target=validate(","let (mut target,cashback)=validate(")]
E['CBR2']=[(")->Result<Pubkey>{",")->Result<(Pubkey,bool)>{"),
 (" Ok(target)}pub fn execute"," Ok((target,cashback))}pub fn execute"),
 ("let cashback=!holder&&st.cashback;let mut target=validate(","let cashback;let mut target;(target,cashback)=validate(")]
