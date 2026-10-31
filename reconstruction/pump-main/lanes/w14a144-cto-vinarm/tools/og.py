# w14a123 origfill genes: (old,new) exact single-occurrence replacements in admin_cto.rs (line count kept)
G={}
_HA="if holder{(false,Some(None),false)}"
G['ha']=[(_HA,"if holder{(false,Some(args.0),false)}")]
G['hn']=[(_HA,"if holder{(false,Some(new),false)}")]
_T1="let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r"
G['t1']=[(_T1,"let r=(false,Some(args.0),true);target=st.creator;r")]
G['su1']=[("if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}",
           "let r=(false,Some(args.0),!holder);if !holder{target=a.bonding_curve.creator;}r")]
G['su2']=[("if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}",
           "if !holder{target=a.bonding_curve.creator;}(false,Some(args.0),!holder)")]
_SIG=(",sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);",",sharing:&Pubkey,shared:bool)->Result<(Pubkey,bool,Option<Option<Pubkey>>,bool)>{let holder=hopt==Some(true);")
_RET=(" Ok(target)}pub fn execute"," Ok((target,collect_old,sharing_update,skip))}pub fn execute")
_EX=("let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};",
     "let sk=a.sharing_config.key();let (target,collect_old,sharing_update,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;")
_CB="let cashback=if holder{false}else{st.cashback};\n\n"
def _vin(tree): return [_SIG,_RET,_EX,(_CB,"let cashback=if holder{false}else{st.cashback};\n "+tree+"\n")]
G['vin']=_vin("let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,Some(None),false)}else{(st.creator,false,Some(new),true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
G['vinh']=_vin("let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,Some(new),false)}else{(st.creator,false,Some(new),true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
G['vinm']=_vin("let (target,collect_old,sharing_update,skip)=if !shared{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}else if holder{(target,false,Some(None),false)}else{(st.creator,false,Some(new),true)};")
# tree placed inside the target if: holder arm / else arm carry the shared override (per-arm, before cashback)
# ---- w14a144 vinarm genes ----
G['none']=[]
_HARM=("let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{",)
_NARM=("if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};",)
_TR0="let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,Some(None),false)}else{(st.creator,false,Some(new),true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};"
def _vpl(harm,narm,tree):
    return [_SIG,_RET,_EX,(_HARM[0],harm),(_NARM[0],narm),(_CB,"let cashback=if holder{false}else{st.cashback};\n "+tree+"\n")]
# vpl1: per-arm Option<Option<Pubkey>> local assigned inside each validate target arm (before cashback/fee), tree uses it
G['vpl1']=_vpl("let mut su:Option<Option<Pubkey>>=None;let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if shared{su=Some(new);}*holder_key}else{",
  "if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if shared{su=Some(new);}t};",
  "let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,su,false)}else{(st.creator,false,su,true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
# vpl2: as vpl1 but the shared target override also sits in the non-holder arm (per-arm tree head)
G['vpl2']=_vpl("let mut su:Option<Option<Pubkey>>=None;let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if shared{su=Some(new);}*holder_key}else{",
  "if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if shared{su=Some(new);st.creator}else{t}};",
  "let (collect_old,skip)=if shared{(false,!holder)}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};let sharing_update=su;")
# vpl3: su local per arm with the holder arm's payload copied from new (Some(None) with new's dead payload), tree keeps st.creator override
G['vpl3']=_vpl("let su:Option<Option<Pubkey>>;let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}su=if shared{Some(new)}else{None};*holder_key}else{",
  "if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}su=if shared{Some(new)}else{None};t};",
  "let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,su,false)}else{(st.creator,false,su,true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),su,true)};")
# pl1: execute-level per-arm payload local (no vin)
_EXT="let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};"
G['pl1']=[(_EXT,"let sharing_update:Option<Option<Pubkey>>;let (collect_old,skip)=if shared{if holder{sharing_update=Some(args.0);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{sharing_update=None;(!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
G['pl2']=[(_EXT,"let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
# vins: control - same tuple-returning validate, tree after the fee checks (isolates 'before fee' from the return-type change)
G['vins']=[_SIG,(" Ok(target)}pub fn execute"," "+_TR0+" Ok((target,collect_old,sharing_update,skip))}pub fn execute"),_EX]
# vinr: tree before fee checks but holder/shared flags of the tree read as one match on (shared,holder)
G['vinr']=_vin("let (target,collect_old,sharing_update,skip)=match (shared,holder){(true,true)=>(target,false,Some(None),false),(true,false)=>(st.creator,false,Some(new),true),_=>(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
# pl2 family (pl2 = 0.67346 @27400 on ebe5387)
_C="(!st.holder_reward&&st.creator!=Pubkey::default(),true)"
_TG="target=a.bonding_curve.creator;"
def _pl(s): return [(_EXT,s)]
G['pl3']=_pl("let mut sharing_update=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);"+_TG+"(false,true)}}else{"+_C+"};")
G['pl5']=_pl("let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{"+_TG+"sharing_update=Some(args.0);(false,true)}}else{"+_C+"};")
G['pl6']=_pl("let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(new);"+_TG+"(false,true)}}else{"+_C+"};")
G['pl7']=_pl("let mut sharing_update:Option<Option<Pubkey>>=None;let mut collect_old=false;let mut skip=true;if shared{if holder{sharing_update=Some(None);skip=false;}else{sharing_update=Some(args.0);"+_TG+"}}else{collect_old=!st.holder_reward&&st.creator!=Pubkey::default();}")
G['pl10']=_pl("let sharing_update:Option<Option<Pubkey>>;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);"+_TG+"(false,true)}}else{sharing_update=None;"+_C+"};")
G['pl11']=_pl("let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if !shared{"+_C+"}else if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);"+_TG+"(false,true)};")
G['pl12']=_pl("let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{sharing_update=Some(if holder{None}else{"+_TG+"args.0});(false,!holder)}else{"+_C+"};")
G['pl13']=_pl("let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{let r=(false,true);sharing_update=Some(args.0);"+_TG+"r}}else{"+_C+"};")
G['pl14']=_pl("let mut sharing_update=None::<Option<Pubkey>>;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);"+_TG+"(false,true)}}else{"+_C+"};")
# ---- wave 2 genes: on main e88f9d559 (pl2 landed) ----
_P2="let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
_CO="!st.holder_reward&&st.creator!=Pubkey::default()"
G['w2a']=[(_P2,"let mut sharing_update:Option<Option<Pubkey>>=None;let mut collect_old=false;let skip=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;true}}else{collect_old="+_CO+";true};")]
G['w2b']=[(_P2,"let mut sharing_update:Option<Option<Pubkey>>=None;let mut skip=true;let collect_old=if shared{if holder{sharing_update=Some(None);skip=false;false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;false}}else{"+_CO+"};")]
G['w2c']=[("let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;",
           "let mut sharing_update:Option<Option<Pubkey>>=None;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['w2d']=[("let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st=","let mut sharing_update:Option<Option<Pubkey>>=None;let (_holder,cashback,target,collect_old,skip)={ let st="),
           ("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),
           ("(holder,cashback,target,sharing_update,collect_old,skip)};","(holder,cashback,target,collect_old,skip)};")]
G['w2e']=[("let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;","let (target,cashback)=Ok::<_,anchor_lang::error::Error>((target,cashback))?;")]
G['w2f']=G['w2d']+G['w2e']
G['w2g']=[(_P2,"let mut sharing_update:Option<Option<Pubkey>>=None;let mut collect_old=false;let mut skip=true;if shared{skip=holder==false;if holder{sharing_update=Some(None);}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;}}else{collect_old="+_CO+";}")]
G['w2h']=[(_P2,"let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{target=a.bonding_curve.creator;sharing_update=Some(new);(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
G['w3a']=[("let (old_creator,old_fee)={\n  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;","let old_creator;let old_fee;{\n  let curve=&mut ctx.accounts.bonding_curve;old_creator=curve.creator;old_fee=curve.creator_fee_bps;"),
          ("\n (old_creator,old_fee)};","\n }")]
G['w3b']=[("let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st=","let cashback;let (_holder,target,sharing_update,collect_old,skip)={ let st="),
          ("let cashback=!holder&&st.cashback;let args=","cashback=!holder&&st.cashback;let args="),
          ("(holder,cashback,target,sharing_update,collect_old,skip)};","(holder,target,sharing_update,collect_old,skip)};")]
G['w3c']=[("let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st=","let mut target;let (_holder,cashback,sharing_update,collect_old,skip)={ let st="),
          ("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),
          ("(holder,cashback,target,sharing_update,collect_old,skip)};","(holder,cashback,sharing_update,collect_old,skip)};")]
# ---- wave 4: per-arm deferred-init locals inside validate's target arms ----
_HA4="let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
_NA4="if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
_NT4="  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
_CB4=(" let cashback=if holder{false}else{st.cashback};\n"," \n")
G['v1']=[(_HA4,"let cashback;let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}cashback=false;*holder_key}else{"),
         (_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}cashback=st.cashback;t};"),_CB4]
G['v2']=[(_HA4,"let cashback;let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}cashback=false;*holder_key}else{"),
         (_NT4,"  cashback=st.cashback;let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"),_CB4]
G['v3']=[(_HA4,"let target;if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}target=*holder_key;}else{"),
         (_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}target=t;}")]
G['v4']=[(_HA4,"let target;let cashback;if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}cashback=false;target=*holder_key;}else{"),
         (_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}cashback=st.cashback;target=t;}"),_CB4]
G['v5']=[(_HA4,"let cashback;let target=if holder{cashback=false;if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"),
         (_NT4,"  cashback=st.cashback;let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"),_CB4]
G['v6']=[(_HA4,"let mut cashback=false;let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"),
         (_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}cashback=st.cashback;t};"),_CB4]
# ---- wave 5: split validate: target checks | sharing tree | fee checks (tree before the fee checks, validate keeps returning Pubkey) ----
_VF=(" let cashback=if holder{false}else{st.cashback};\n"," Ok(target)}fn validate_fee(st:&CtoState,holder:bool,fee:Option<u64>,holder_key:&Pubkey)->Result<()>{let cashback=if holder{false}else{st.cashback};\n")
_VR=(" Ok(target)}pub fn execute"," Ok(())}pub fn execute")
_TREE="let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
G['vsp1']=[_VF,_VR,(_TREE,_TREE+"validate_fee(&st,holder,fee,&holder_key)?;")]
G['vsp2']=[_VF,_VR,(_TREE,"let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);validate_fee(&st,holder,fee,&holder_key)?;(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;validate_fee(&st,holder,fee,&holder_key)?;(false,true)}}else{validate_fee(&st,holder,fee,&holder_key)?;(!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
G['vsp0']=[_VF,_VR,("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;validate_fee(&st,holder,fee,&holder_key)?;")]
_VFi=(_VF[0],_VF[1].replace("}fn validate_fee","}#[inline] fn validate_fee"))
_VFa=(_VF[0],_VF[1].replace("}fn validate_fee","}#[inline(always)] fn validate_fee"))
G['vsp1i']=[_VFi]+G['vsp1'][1:]
G['vsp1a']=[_VFa]+G['vsp1'][1:]
G['vsp0i']=[_VFi]+G['vsp0'][1:]
G['vsp0a']=[_VFa]+G['vsp0'][1:]
# ---- wave 6: validate fills an &mut sharing_update out-param per arm (keeps Result<Pubkey>) ----
_SIGo=(",sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);",",sharing:&Pubkey,shared:bool,su:&mut Option<Option<Pubkey>>)->Result<Pubkey>{let holder=hopt==Some(true);")
_EXo=("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}",
      "let mut sharing_update:Option<Option<Pubkey>>=None;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared,&mut sharing_update)?;let (collect_old,skip)=if shared{if holder{(false,false)}else{target=a.bonding_curve.creator;(false,true)}}")
_EXo2=("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}",
      "let mut sharing_update:Option<Option<Pubkey>>=None;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared,&mut sharing_update)?;let _=args;let (collect_old,skip)=if shared{if holder{(false,false)}else{target=a.bonding_curve.creator;(false,true)}}")
G['vo1']=[_SIGo,_EXo,(_HA4,"let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if shared{*su=Some(None);}*holder_key}else{"),
          (_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if shared{*su=Some(new);}t};")]
G['vo1n']=[_SIGo,_EXo,(_HA4,"let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if shared{*su=Some(new);}*holder_key}else{"),
          (_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if shared{*su=Some(new);}t};")]
G['vo3']=[_SIGo,_EXo,_CB4,(" Ok(target)}pub fn execute"," Ok(target)}pub fn execute"),(_NA4,_NA4+"let cashback=if holder{false}else{st.cashback};if shared{*su=Some(if holder{None}else{new});}")]
G['vo5']=[_SIGo,_EXo,(" Ok(target)}pub fn execute"," if shared{*su=Some(if holder{None}else{new});}Ok(target)}pub fn execute")]
G['vo6']=[_SIGo,_EXo,(_NA4,"if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}if shared{*su=Some(Some(t));}t};"),(_HA4,"let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if shared{*su=Some(None);}*holder_key}else{")]
# vo1 frame-position variants of the sharing_update declaration
_vo1x=[e for e in G['vo1'] if e is not _EXo]
G['vo1b']=_vo1x+[("let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}",
  "let mut sharing_update:Option<Option<Pubkey>>=None;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared,&mut sharing_update)?;let (collect_old,skip)=if shared{if holder{(false,false)}else{target=a.bonding_curve.creator;(false,true)}}")]
G['vo1c']=_vo1x+[("let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st=","let mut sharing_update:Option<Option<Pubkey>>=None;let (_holder,cashback,target,collect_old,skip)={ let st="),
  ("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}",
   "let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared,&mut sharing_update)?;let (collect_old,skip)=if shared{if holder{(false,false)}else{target=a.bonding_curve.creator;(false,true)}}"),
  ("(holder,cashback,target,sharing_update,collect_old,skip)};","(holder,cashback,target,collect_old,skip)};")]
G['vo1d']=_vo1x+[("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}",
   "let mut su:Option<Option<Pubkey>>=None;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared,&mut su)?;let sharing_update=su;let (collect_old,skip)=if shared{if holder{(false,false)}else{target=a.bonding_curve.creator;(false,true)}}")]
G['pl15']=[(_P2,_P2.replace("if holder{sharing_update=Some(None);(false,false)}","if holder{let r=(false,false);sharing_update=Some(None);r}"))]
G['pl17']=[(_P2,_P2.replace("if holder{sharing_update=Some(None);","if holder{sharing_update=Some(new);"))]
G['pl18']=[(_P2,_P2.replace("if holder{sharing_update=Some(None);(false,false)}","if holder{sharing_update=Some(None);(false,holder&&false)}"))]
G['pl19']=[(_P2,_P2.replace("let mut sharing_update:Option<Option<Pubkey>>=None;","let mut sharing_update:Option<Option<Pubkey>>=Option::None;").replace("sharing_update=Some(None);","sharing_update=Some(Option::None);"))]
