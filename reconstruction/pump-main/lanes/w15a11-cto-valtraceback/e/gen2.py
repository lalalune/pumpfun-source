import json
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a11-cto-valtraceback'
SIG='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>'
CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
L312='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
L298='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
TREE='let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};'
E298='if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}'
E312='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}'
CO='!st.holder_reward&&st.creator!=Pubkey::default()'
V={}
V['ov1']=[(SIG,'holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<Pubkey>'),(L312,E312+'if shared{st.creator}else{t}};'),
  (CALL,'let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;'),('sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)','sharing_update=Some(args.0);(false,true)')]
SIG2='holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<(Pubkey,Option<Option<Pubkey>>,bool,bool)>'
V['ov2']=[(SIG,SIG2),
  (L298,'let (target,su,co,skip)=if holder{'+E298+'if shared{(*holder_key,Some(None),false,false)}else{(*holder_key,None,'+CO+',true)}}else{'),
  (L312,E312+'if shared{(st.creator,Some(new),false,true)}else{(t,None,'+CO+',true)}};'),
  (' Ok(target)}pub fn execute',' Ok((target,su,co,skip))}pub fn execute'),
  (CALL+TREE,'let (target,sharing_update,collect_old,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;')]
# ov3: tree only in nonholder arm; holder arm keeps execute-side tree
V['ov3']=[(SIG,'holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<(Pubkey,Option<Option<Pubkey>>,bool,bool)>'),
  (L298,'let (target,su,co,skip)=if holder{'+E298+'(*holder_key,if shared{Some(None)}else{None},!shared&&'+CO+',!shared)}else{'),
  (L312,E312+'if shared{(st.creator,Some(new),false,true)}else{(t,None,'+CO+',true)}};'),
  (' Ok(target)}pub fn execute',' Ok((target,su,co,skip))}pub fn execute'),
  (CALL+TREE,'let (target,sharing_update,collect_old,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;')]
# ov4: ov2 with a.bonding_curve-free tuple but shared tested first in arms (match)
V['ov4']=[(SIG,SIG2),
  (L298,'let (target,su,co,skip)=if holder{'+E298+'match shared{true=>(*holder_key,Some(None),false,false),false=>(*holder_key,None,'+CO+',true)}}else{'),
  (L312,E312+'match shared{true=>(st.creator,Some(new),false,true),false=>(t,None,'+CO+',true)}};'),
  (' Ok(target)}pub fn execute',' Ok((target,su,co,skip))}pub fn execute'),
  (CALL+TREE,'let (target,sharing_update,collect_old,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;')]
for k,v in V.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
