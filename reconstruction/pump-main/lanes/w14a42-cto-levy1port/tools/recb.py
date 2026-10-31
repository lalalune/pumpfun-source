#!/usr/bin/env python3
"""recb.py <sha7> <hyp-prefix> <jsonl..>: record every result row (with M/jM from mr.py) in the ledger."""
import sys,json,subprocess,os
sha,hp=sys.argv[1:3]; files=sys.argv[3:]
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a42-cto-levy1port/reconstruction/pump-main/log_attempt.py'
out=subprocess.run(['python3',os.path.dirname(os.path.abspath(__file__))+'/mr.py']+files,capture_output=True,text=True).stdout
spec={}
for f in files:
    for l in open(f):
        r=json.loads(l); spec[r['name']]=r
n=0
for l in out.split('\n'):
    p=l.split()
    if len(p)<7: continue
    nm=p[0]; ratio=float(p[1]); b=int(p[2]); M=int(p[4]); J=int(p[6])
    try: E=open(f'src_edits/{nm}.py').read()[:1500]
    except Exception: E=''
    d={'output':f'$OUT/rx/{nm}','losses':[],'raw_losses':[],'target':{'ratio':ratio,'slots_diff':None,'cand_bytes':b},'notes':f'raw-IR capture+opt+llc oracle on main {sha} (m eq_main): ratio {ratio} bytes {b} M {M} jM {J}'}
    st='analyzed' if nm in('n_m','m') else 'rejected'
    subprocess.run(['python3',L,'record','--lane','w14a42-cto-levy1port','--approach','levy1port','--target','0x22a10','--dedupe-key',f'0x22a10-w14-{sha}-levy1port-{nm}-v1','--hypothesis',hp+' '+nm+': '+E,'--status',st,'--data',json.dumps(d)],capture_output=True); n+=1
print('recorded',n)
