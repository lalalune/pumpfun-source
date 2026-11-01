import json,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour'
D="let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
V={}
# flag set per arm in the post-validate decision (no out-param in validate)
V['Hdf']=[("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut hf;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),
 (D,"let (collect_old,skip)=if shared{if holder{hf=true;sharing_update=Some(None);(false,false)}else{hf=false;sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{hf=holder;(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"),
 ("(holder,cashback,target,sharing_update,collect_old,skip)}","(hf,cashback,target,sharing_update,collect_old,skip)}"),
 ("curve.is_holder_reward=holder.unwrap_or(false);","curve.is_holder_reward=_holder;"),
 ("is_holder_reward:a.bonding_curve.is_holder_reward,","is_holder_reward:holder.unwrap_or(false),")]
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a20-cto-s3flagcolour/programs/pump/src/creator/admin_cto.rs').read()
for k,v in V.items():
    s=src; n0=s.count('\n')
    for a,b in v:
        c=s.count(a); assert c==1,(k,c,a[:90]); s=s.replace(a,b)
    assert s.count('\n')==n0,(k,'lines')
    open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n'); print(k,len(v),'ok')
