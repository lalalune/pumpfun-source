import json,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour'
S3=[tuple(x) for x in runpy.run_path(O+'/e/S3n.py')['EDITS']]
def rep(lst,old,new):
    out=[]; hit=0
    for a,b in lst:
        if old in b: b=b.replace(old,new); hit+=1
        out.append((a,b))
    assert hit==1,(old,hit); return out
V={}
# H1 Option<bool> carrier
o=rep(S3,"hf:&mut bool)","hf:&mut Option<bool>)"); o=rep(o,"*hf=true;","*hf=Some(true);"); o=rep(o,"*hf=false;","*hf=Some(false);"); o=rep(o,"let mut hf=false;","let mut hf=None;"); o=rep(o,"curve.is_holder_reward=_holder;","curve.is_holder_reward=_holder.unwrap_or(false);")
V['Hopt']=o
# H2 hf declared at the top of execute (before the a binding)
h=rep(S3,"let mut hf=false;let mut target=validate(","let mut target=validate(")
V['Htop']=h+[("->Result<()>{ let a=&ctx.accounts;let mint=a.mint.key();","->Result<()>{ let mut hf=false;let a=&ctx.accounts;let mint=a.mint.key();")]
# H3 decision as a tuple match on (shared,hf)
V['Hmatch']=S3+[("let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};",
 "let (collect_old,skip)=match (shared,hf){(true,true)=>{sharing_update=Some(None);(false,false)}(true,false)=>{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}(false,_)=>(!st.holder_reward&&st.creator!=Pubkey::default(),true)};")]
# H4 curve flag store first in the curve block
V['Hcsfirst']=rep(S3,"curve.is_holder_reward=_holder;","")+[("let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;","let curve=&mut ctx.accounts.bonding_curve;curve.is_holder_reward=_holder;let old_creator=curve.creator;")]
# H5 validate cashback from the just-written flag
V['Hvcb']=S3+[(" let cashback=if holder{false}else{st.cashback};"," let cashback=if *hf{false}else{st.cashback};")]
# H6 Fdec + H5
V['Hdecvcb']=V['Hvcb']+[("let (collect_old,skip)=if shared{if holder{","let (collect_old,skip)=if shared{if hf{")]
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a20-cto-s3flagcolour/programs/pump/src/creator/admin_cto.rs').read()
for k,v in V.items():
    s=src; n0=s.count('\n')
    for a,b in v:
        c=s.count(a); assert c==1,(k,c,a[:90]); s=s.replace(a,b)
    assert s.count('\n')==n0,(k,'lines')
    open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n'); print(k,len(v),'ok')
