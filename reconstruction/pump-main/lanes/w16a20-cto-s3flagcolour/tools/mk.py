import json,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour'
S3=[tuple(x) for x in runpy.run_path(O+'/e/S3n.py')['EDITS']]
def rep(lst,old,new):
    out=[]; hit=0
    for a,b in lst:
        if old in b: b=b.replace(old,new); hit+=1
        out.append((a,b))
    assert hit==1,(old,hit); return out
P=lambda l:l
V={}
# F_pool: pool CPI arg from the flag (orig 0x4e20 r4 = flag)
V['Fpool']=S3+[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(target,_holder,fee);")]
# F_ev: event is_holder_reward from the flag
V['Fev']=rep(S3,"is_holder_reward:holder.unwrap_or(false),","is_holder_reward:_holder,")
V['Fboth']=rep(V['Fpool'],"is_holder_reward:holder.unwrap_or(false),","is_holder_reward:_holder,")
# F_dec: post-validate shared decision reads the flag
V['Fdec']=S3+[("let (collect_old,skip)=if shared{if holder{","let (collect_old,skip)=if shared{if hf{")]
# F_u8: flag as u8
u=rep(S3,"hf:&mut bool)","hf:&mut u8)"); u=rep(u,"*hf=true;","*hf=1;"); u=rep(u,"*hf=false;","*hf=0;"); u=rep(u,"let mut hf=false;","let mut hf=0u8;"); u=rep(u,"curve.is_holder_reward=_holder;","curve.is_holder_reward=_holder!=0;")
V['Fu8']=u
# F_end: single write *hf=holder before Ok(target) (no per-arm writes)
e=[x for x in S3 if '*hf=true' not in x[1] and '*hf=false' not in x[1]]
V['Fend']=e+[(" Ok(target)}pub fn execute"," *hf=holder;Ok(target)}pub fn execute")]
V['Fdecpool']=V['Fdec']+[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(target,_holder,fee);")]
V['Fdecev']=rep(V['Fdec'],"is_holder_reward:holder.unwrap_or(false),","is_holder_reward:_holder,")
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a20-cto-s3flagcolour/programs/pump/src/creator/admin_cto.rs').read()
for k,v in V.items():
    s=src; n0=s.count('\n')
    for a,b in v:
        c=s.count(a); assert c==1,(k,c,a[:90]); s=s.replace(a,b)
    assert s.count('\n')==n0,(k,'lines')
    open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n'); print(k,len(v),'ok')
