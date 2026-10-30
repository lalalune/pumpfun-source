#!/usr/bin/env python3
"""rec2.py <res.txt> <sha7> <main_ratio>: record each trial line to the shared ledger (dedupe-checked)."""
import sys,json,subprocess,runpy,os
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a29-cto-hcbools/reconstruction/pump-main/log_attempt.py'
E='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a29-cto-hcbools/edits/'
res,sha,mr=sys.argv[1],sys.argv[2],float(sys.argv[3])
for l in open(res):
    js,_,cr=l.strip().rpartition(' ')
    r=json.loads(js); n=r['name']
    if n=='main': continue
    ed=runpy.run_path(E+n+'.py')['EDITS']
    hyp='hcbools %s: '%n+'; '.join('%r -> %r'%(a[:90],b[:160]) for a,b in ed)
    key='0x22a10-w14-%s-hcbools-%s-v1'%(sha,n)
    if subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True).returncode!=0: print('dup',key); continue
    better=r['bytes']==27400 and r['ratio']>mr
    st='partial' if better else 'rejected'
    note='raw-IR capture + rx opt/llc oracle (= identity build) on main %s (%.5f): ratio %s bytes %s slots %s; sharing-CPI crossing spill intervals %s (orig 8, main 10)'%(sha,mr,r['ratio'],r['bytes'],r['slots_diff'],cr)
    d={'output':'rx/'+n,'target':{'ratio':r['ratio'],'slots_diff':r['slots_diff'],'cand_bytes':r['bytes']},'notes':note}
    p=subprocess.run(['python3',L,'record','--lane','w14a29-cto-hcbools','--approach','hcbools','--target','0x22a10','--dedupe-key',key,'--hypothesis',hyp,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    print(n,st,p.returncode,p.stderr[-200:])
