#!/usr/bin/env python3
"""rec25.py [names...]: record trig.txt rows in the shared ledger (approach o2tfg3repay)"""
import sys,re,json,subprocess,os
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a25-cto-o2tfg3repay'
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import g25
want=set(sys.argv[1:]); LCS={}
if os.path.exists('lcs.txt'):
    for l in open('lcs.txt'):
        p=l.split()
        if len(p)>=4: LCS[p[0]]=(p[2],p[3])
for l in open('trig.txt'):
    n=l.split()[0]; g=l.split()[1]
    if want and n not in want: continue
    if n in('m0',): continue
    m=re.search(r'B (\d+) M (\d+) fM (\d+) rM (\d+) rfM (\d+) rfjM (\d+)',l); r=re.search(r'"ratio": ([\d.]+)',l); k=re.search(r'calls (\d+) lddw (\d+)',l)
    pat='orig-pattern=True' in l; i=l.split('|')[1].strip()
    if not m:
        st='compile-failed'; tgt={}; note='compile failed: '+l.split('|')[-1][:200]
    else:
        st='rejected'; tgt={'ratio':float(r[1]),'cand_bytes':int(m[1]),'slots_diff':None}
        note=f"raw-IR capture + opt -O3 + llc oracle on main 9120883 (m0 eq_main, 0.67376 M2249 @27400). M {m[2]} fM {m[3]} rM {m[4]} rfM {m[5]} rfjM {m[6]}; calls {k[1]} lddw {k[2]}; outline map {i}; trueLCS {LCS.get(n,('?','?'))}"
    ed=[]
    for x in g.split('+'):
        ed+=g25.G.get(x,[('gene',x)])
    hyp=f"o2tfg3repay {n} ({g}): 307+312 to_string outline source trigger / O-repay grid; edits={json.dumps(ed)[:1500]}"
    key=f"0x22a10-w15-9120883-o2tfg3repay-{n}-v1"
    d={'output':f'rx/{n}','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':tgt,'notes':note}
    subprocess.run(['python3',WT+'/reconstruction/pump-main/log_attempt.py','record','--lane','w15a25-cto-o2tfg3repay','--approach','o2tfg3repay','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],check=False,capture_output=True)
    print('rec',n,st)
