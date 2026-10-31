import json,os
E=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a52-cto-prep410/e')
T0="let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};"
SUF="let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
O0="(holder,cashback,target,sharing_update,collect_old,skip)};"
L0="let (holder,cashback,target,sharing_update,collect_old,skip)={"
OK0="let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
V={}
def outer(perm): return [(L0,"let ("+perm+")={"),(O0,"("+perm+")};")]
for nm,perm in [('o_su1','holder,cashback,sharing_update,target,collect_old,skip'),('o_su2','sharing_update,holder,cashback,target,collect_old,skip'),('o_su3','holder,cashback,target,collect_old,skip,sharing_update'),('o_su4','holder,cashback,target,sharing_update,skip,collect_old'),('o_su5','holder,sharing_update,cashback,target,collect_old,skip')]:
    V[nm]=outer(perm); V[nm+'s']=[(T0,SUF)]+outer(perm)
V['s_sukip']=[(T0,"let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};")] # = suf sanity
V['s_suf_ok']=[(T0,SUF),(OK0,"let (sharing_update,target,cashback)=Ok::<_,anchor_lang::error::Error>((sharing_update,target,cashback))?;")]
V['s_su_cs']=[(T0,"let (sharing_update,skip,collect_old)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),true,false)}}else{(None,true,!st.holder_reward&&st.creator!=Pubkey::default())};")]
V['s_suf_hnot']=[(T0,"let (sharing_update,collect_old,skip)=if shared{if !holder{target=st.creator;(Some(args.0),false,true)}else{(Some(None),false,false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
V['s_suf_new']=[(T0,"let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
V['s_suf_co2']=[(T0,"let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,st.creator!=Pubkey::default()&&!st.holder_reward,true)};")]
for k,v in V.items(): open(f'{E}/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
