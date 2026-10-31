G={}
SIG="new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
CALL="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
TREE="let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};"
HARM="return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
NEND="if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
NOV="(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)"
# OV: shared target override inside the non-holder arm
G['ov']=[(SIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<Pubkey>{"),
 (NEND,NEND[:-3]+"if shared{st.creator}else{t}};"),
 (CALL,"let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;"),
 ("let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r","(false,Some(args.0),true)")]
# OVT: whole sharing tree computed per arm inside validate, before the fee checks
G['ovt']=[(SIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<(Pubkey,bool,Option<Option<Pubkey>>,bool)>{"),
 (HARM,"return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if shared{(*holder_key,false,Some(None),false)}else{let k=*holder_key;(k,"+NOV[1:]+"}}else{"),
 (NEND,NEND[:-3]+"if shared{(st.creator,false,Some(Some(t)),true)}else{(t,"+NOV[1:]+"}};"),
 (CALL+TREE,"let (target,collect_old,sharing_update,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;let _=args;")]
# OVT2: same, non-holder shared arm carries new (args.0) instead of Some(t)
G['ovt2']=[G['ovt'][0],G['ovt'][1],(NEND,NEND[:-3]+"if shared{(st.creator,false,Some(new),true)}else{(t,"+NOV[1:]+"}};"),G['ovt'][3]]
D={'ov':'shared target override inside validate non-holder arm (validate takes shared; arm yields if shared{st.creator}else{t}; execute drops target=creator) - decodes orig 0x0d90-0x0e08 st.creator copy',
 'ovt':'whole sharing tree (target,collect_old,sharing_update,skip) per arm inside validate before fee checks - decodes orig runs 0x0d90/0x10f0/0x14b0 (per-arm phi stores)',
 'ovt2':'ovt with Some(new) instead of Some(Some(t)) in the shared non-holder arm'}
G['ov2']=G['ov'][:3]
D['ov2']='ov but execute keeps target=a.bonding_curve.creator (tests whether the 660 flip in ov comes from dropping the execute assignment)'
G['ovs']=[G['ov'][0],(NEND,NEND[:-3]+"if shared{return Ok(st.creator)}t};"),G['ov'][2],G['ov'][3]]
D['ovs']='ov with an early return Ok(st.creator) for shared (skips fee checks; semantic change, probe only)'
OVTREE="let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};"
def ovx(newtree): return G['ov'][:3]+[(TREE,newtree)]
G['ov_a']=ovx("let (collect_old,sharing_update,skip)=if shared&&holder{(false,Some(None),false)}else if shared{(false,Some(args.0),true)}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
G['ov_b']=ovx("let skip=!(shared&&holder);let (collect_old,sharing_update)=if shared{if holder{(false,Some(None))}else{(false,Some(args.0))}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None)};")
G['ov_c']=ovx("let (collect_old,sharing_update,skip)=if holder&&shared{(false,Some(None),false)}else if shared{(false,Some(args.0),true)}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
G['ov_d']=ovx("let (collect_old,sharing_update,skip)=if !shared{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}else if holder{(false,Some(None),false)}else{(false,Some(args.0),true)};")
G['ov_e']=[(SIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,ov:Option<Pubkey>)->Result<Pubkey>{"),
 (NEND,NEND[:-3]+"ov.unwrap_or(t)};"),
 (CALL,"let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared.then_some(st.creator))?;"),
 ("let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r","(false,Some(args.0),true)")]
G['ov_f']=[(SIG,"new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,ov:Option<&Pubkey>)->Result<Pubkey>{"),
 (NEND,NEND[:-3]+"if let Some(c)=ov{*c}else{t}};"),
 (CALL,"let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared.then_some(&st.creator))?;"),
 ("let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r","(false,Some(args.0),true)")]
D.update({'ov_a':'ov + tree as if shared&&holder / else if shared / else','ov_b':'ov + skip=!(shared&&holder) split from the (collect_old,sharing_update) tree',
 'ov_c':'ov + tree if holder&&shared / else if shared / else','ov_d':'ov + tree !shared arm first',
 'ov_e':'override passed as ov:Option<Pubkey>=shared.then_some(st.creator), arm ov.unwrap_or(t)','ov_f':'override passed as Option<&Pubkey>=shared.then_some(&st.creator), arm if let Some(c)=ov{*c}else{t}'})
