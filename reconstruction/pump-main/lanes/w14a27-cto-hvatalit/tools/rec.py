#!/usr/bin/env python3
"""rec.py <resfile> <edir> <group> <hyp-prefix>: record every result of a screen in the shared ledger."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a27-cto-hvatalit/reconstruction/pump-main/log_attempt.py'
res,ed,grp,hp=sys.argv[1:5]
import os
SHA=os.environ.get('SHA','7e6aa9c'); MAIN=os.environ.get('MAIN','main 7e6aa9c (0.6414, 3173 slots, 157 calls).'); BR=float(os.environ.get('BR','0.6414'))
for l in open(res):
    r=json.loads(l); n=r['name']
    try: e=open(f'{ed}/{n}.py').read()
    except: e=''
    ok='ratio' in r
    st='rejected' if ok else 'compile-failed'
    if ok and r['ratio']==BR and r['bytes']==27400: note='same ratio as main (%s, 27400 B)'%BR
    elif ok: note='ratio %s bytes %s calls %s (orig 157)'%(r['ratio'],r['bytes'],r.get('calls'))
    else: note='compile error'
    d={'output':'raw-IR capture + rx oracle (opt -O3 + llc)','normalized':None,'raw':None,'target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes'),'calls':r.get('calls')},'notes':MAIN+' '+note+' edits: '+e[:700]}
    k='0x22a10-w14-%s-hvatalit-%s-%s-v1'%(SHA,grp,n)
    p=subprocess.run(['python3',L,'record','--lane','w14a27-cto-hvatalit','--approach','hvatalit','--target','0x22a10','--dedupe-key',k,'--hypothesis',hp+' '+n,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    print(n, (p.stdout+p.stderr).strip()[-80:])
