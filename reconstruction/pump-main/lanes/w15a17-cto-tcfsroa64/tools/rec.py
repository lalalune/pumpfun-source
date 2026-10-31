import json,subprocess,sys,re
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a17-cto-tcfsroa64/reconstruction/pump-main/log_attempt.py'
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a17-cto-tcfsroa64'
H=json.load(open(sys.argv[1]))
for n,h in H.items():
    r=json.load(open(f'{O}/rx/{n}/res.json'))
    a=subprocess.run(['python3',O+'/tools/alt.py',f'{O}/rx/{n}/m.ll'],capture_output=True,text=True).stdout
    pads=len(re.findall(r'\.sroa\.11\.i\[5\]',a.split('\n')[0]))
    st='analyzed' if r.get('eq_main') else 'rejected'
    d={'output':f'rx/{n}','target':r,'notes':f'raw-IR capture + opt/llc oracle on main 86e2a6b (0.67376@27400); TCF [5 x i8] padding allocas left: {pads} of 4 (orig has all 4 padding copies at the same frame offsets); eq_main {r.get("eq_main")}'}
    p=subprocess.run(['python3',L,'record','--lane','w15a17-cto-tcfsroa64','--approach','tcfsroa64','--target','0x22a10','--dedupe-key',f'0x22a10-w15-86e2a6b-tcfsroa64-{n}-v1','--hypothesis',h,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    print(n,pads,r['ratio'],r['bytes'],p.returncode,p.stderr[-200:])
