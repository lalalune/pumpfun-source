#!/usr/bin/env python3
"""rec.py results.jsonl 'hypothesis prefix' [sha7]: record every row as a ledger trial (oracle results)."""
import sys,json,subprocess
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a76-cto-threehop/reconstruction/pump-main/log_attempt.py'
f,hyp=sys.argv[1],sys.argv[2]; sha=sys.argv[3] if len(sys.argv)>3 else '39eb377'
G='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a76-cto-threehop/gen/'
for l in open(f):
    r=json.loads(l); n=r['n']; x=r.get('px') or r.get('rx') or {}
    key=f'0x22a10-w14-{sha}-threehop-{n}-v1'
    c=subprocess.run(['python3',L,'check','--dedupe-key',key],capture_output=True,text=True)
    if '"duplicate": true' in c.stdout or c.returncode!=0: print('skip',key,c.stdout.strip()[:80]); continue
    try: edits=open(G+n+'.py').read()[:1500]
    except Exception: edits=''
    d={'output':'oracle (raw-IR capture + opt/llc)','target':{'ratio':x.get('ratio'),'slots_diff':x.get('slots'),'cand_bytes':x.get('bytes')},'notes':f"fm {x.get('fm')} sk {x.get('sk')} err {x.get('err')}; base main 0.66477@27400. "+r.get('note','')}
    st='rejected' if (x.get('ratio') or 0)<0.66477 or x.get('bytes')!=27400 else 'analyzed'
    subprocess.run(['python3',L,'record','--lane','w14a76-cto-threehop','--approach','threehop','--target','0x22a10','--dedupe-key',key,'--hypothesis',f'{hyp} {n}: {edits}','--status',st,'--data',json.dumps(d)],check=True,capture_output=True)
    print('rec',key,st,x.get('ratio'),x.get('bytes'))
