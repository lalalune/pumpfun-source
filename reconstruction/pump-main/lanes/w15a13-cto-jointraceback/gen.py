import os
SU='let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};'
OKH='let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=target;'
VAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
PREP=' crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;'
SW='swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);'
WG='if collect_old{wallet(&ctx)?;}'
V={}
# a: join constants / phi forms
V['a1']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (skip,collect_old)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(true,false)}}else{(true,!st.holder_reward&&st.creator!=Pubkey::default())};(holder,cashback,target,sharing_update,collect_old,skip)};')],'join tuple order (skip,collect_old)')
V['a2']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let collect_old=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;false}}else{!st.holder_reward&&st.creator!=Pubkey::default()};let skip=!(shared&&holder);(holder,cashback,target,sharing_update,collect_old,skip)};')],'skip as expression !(shared&&holder) after the tree; tree yields collect_old only')
V['a3']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let mut skip=true;let collect_old=if shared{if holder{sharing_update=Some(None);skip=false;false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;false}}else{!st.holder_reward&&st.creator!=Pubkey::default()};(holder,cashback,target,sharing_update,collect_old,skip)};')],'skip as mut local init true, cleared in holder-shared arm')
V['a4']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let mut collect_old=false;let skip=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;true}}else{collect_old=!st.holder_reward&&st.creator!=Pubkey::default();true};(holder,cashback,target,sharing_update,collect_old,skip)};')],'collect_old as mut local set in non-shared arm; tree yields skip')
V['a5']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let mut collect_old=false;let mut skip=true;if shared{if holder{sharing_update=Some(None);skip=false;}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;}}else{collect_old=!st.holder_reward&&st.creator!=Pubkey::default();}(holder,cashback,target,sharing_update,collect_old,skip)};')],'all three join outputs as mut locals (statement tree)')
V['a6']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if !shared{(!st.holder_reward&&st.creator!=Pubkey::default(),true)}else{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}};(holder,cashback,target,sharing_update,collect_old,skip)};')],'!shared arm first (if-else nesting kept)')
V['a7']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if !holder{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}else{sharing_update=Some(None);(false,false)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};')],'inner !holder arm first')
V['a8']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{target=a.bonding_curve.creator;sharing_update=Some(args.0);(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};')],'target override before sharing payload in the shared non-holder arm')
V['a9']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(st.creator!=Pubkey::default()&&!st.holder_reward,true)};(holder,cashback,target,sharing_update,collect_old,skip)};')],'collect_old operand order: creator test first')
V['a10']=([(SU,'let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(if st.holder_reward{false}else{st.creator!=Pubkey::default()},true)};(holder,cashback,target,sharing_update,collect_old,skip)};')],'collect_old as if holder_reward{false}else{creator!=default}')
# b: Ok hop and tuple shape
V['b1']=([(OKH,'let (target,sharing_update,cashback,skip)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,skip))?;let mut target=target;')],'Ok hop carries skip')
V['b2']=([(OKH,'let (target,sharing_update,cashback,collect_old)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,collect_old))?;let mut target=target;')],'Ok hop carries collect_old')
V['b3']=([(OKH,'let (sharing_update,target,cashback)=Ok::<_,anchor_lang::error::Error>((sharing_update,target,cashback))?;let mut target=target;')],'Ok hop field order (sharing_update,target,cashback)')
V['b4']=([(OKH,'let (target,cashback,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,cashback,sharing_update))?;let mut target=target;')],'Ok hop field order (target,cashback,sharing_update)')
V['b5']=([(OKH,'let (cashback,target,sharing_update)=Ok::<_,anchor_lang::error::Error>((cashback,target,sharing_update))?;let mut target=target;')],'Ok hop field order (cashback,target,sharing_update)')
V['b6']=([('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,skip,collect_old)={'),('(holder,cashback,target,sharing_update,collect_old,skip)};','(holder,cashback,target,sharing_update,skip,collect_old)};')],'block tuple field order skip before collect_old')
V['b7']=([('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (collect_old,skip,_holder,cashback,target,sharing_update)={'),('(holder,cashback,target,sharing_update,collect_old,skip)};','(collect_old,skip,holder,cashback,target,sharing_update)};')],'block tuple: flags first')
V['b8']=([('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,sharing_update,target,collect_old,skip)={'),('(holder,cashback,target,sharing_update,collect_old,skip)};','(holder,cashback,sharing_update,target,collect_old,skip)};')],'block tuple: sharing_update before target')
# c: post-join consumers
V['c1']=([(WG,'if collect_old{wallet(&ctx)?}')],'wallet gate without ; (expression)')
V['c2']=([(WG,'collect_old.then(||wallet(&ctx)).transpose()?;')],'wallet gate as then().transpose()?')
V['c3']=([(WG,'if collect_old{let ()=wallet(&ctx)?;}')],'wallet gate let ()=..?')
V['c4']=([(WG,'if !collect_old{}else{wallet(&ctx)?;}')],'wallet gate inverted if')
V['c5']=([(SW,'swept=(!skip).then(||sweep(&ctx,&holder_key)).unwrap_or(Ok(0))?;')],'sweep gate unwrap_or(Ok(0))?')
V['c6']=([(SW,'swept=skip.then_some(Ok(0)).unwrap_or_else(||sweep(&ctx,&holder_key))?;')],'sweep gate skip.then_some(Ok(0)).unwrap_or_else(sweep)?')
V['c7']=([(SW,'swept=if let false=skip{sweep(&ctx,&holder_key)?}else{0};')],'sweep gate if let false=skip')
V['c8']=([(SW,'swept=match skip{false=>sweep(&ctx,&holder_key)?,true=>0};')],'sweep gate match skip false first')
V['c9']=([(SW,'swept=match skip{true=>0,false=>sweep(&ctx,&holder_key)?};')],'sweep gate match skip true first')
for k,(ed,h) in V.items():
    open(f'e/{k}.py','w').write(f'EDITS={ed!r}\nHYP={h!r}\n')
print(' '.join(V))
