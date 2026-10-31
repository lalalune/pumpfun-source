#!/usr/bin/env python3
"""recO.py: record resO.txt (vr.sh lines: plain, _O = 307+312 noinline, _O312 = 312 noinline) rows in the ledger"""
import sys,os,re,subprocess,json
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a21-cto-creatorcopy/reconstruction/pump-main/log_attempt.py'
B=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
done_f=OUT+'/resO.txt.recorded'; done=set(open(done_f).read().split()) if os.path.exists(done_f) else set()
for l in open(OUT+'/resO.txt'):
    n,g=l.split()[:2]
    if n in done or n=='Onone': continue
    parts=re.findall(r'(\S+)\s+B (\d+) M (\d+) fM \d+ rM \d+ rfM \d+ rfjM (\d+)',l)
    lc={}
    for p,_,_,_ in parts:
        o=subprocess.run(['python3',T+'/lcs.py',p,'--masks','---,rfj'],capture_output=True,text=True,cwd=OUT).stdout.split(); lc[p]=' '.join(o[2:])
    note='; '.join(f'{p}: {b} B M {m} rfjM {r} LCS {lc[p]}' for p,b,m,r in parts)+f' (refs Onone_O 26992 B M 1955 LCS ---:2043; Onone_O312 27184 B M 2196 LCS ---:2244; main 27400 M 2249 LCS ---:2255)'
    data={'output':f'rx/{n}* (oracle)','normalized':None,'raw':None,'losses':[],'raw_losses':[],'target':{'ratio':None,'slots_diff':None,'cand_bytes':int(parts[1][1])},'notes':note}
    r=subprocess.run(['python3',L,'record','--lane','w15a21-cto-creatorcopy','--approach','creatorcopy','--target','0x22a10','--dedupe-key',f'0x22a10-w15-{B}-creatorcopy-outline-{n}-v1',
        '--hypothesis',f'creatorcopy gene {g} on the IR outline bases O (307+312 to_string noinline, w15a09 ed/ni.py) and O312 (312 only)','--status','analyzed','--data',json.dumps(data)],capture_output=True,text=True)
    if r.returncode: print('FAIL',n,r.stderr[-200:]); continue
    open(done_f,'a').write(n+'\n'); print('recorded',n)
