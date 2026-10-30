#!/usr/bin/env python3
"""bulkrec.py prefix... : record every res.jsonl row whose name starts with a prefix (once per name) into the ledger."""
import sys,json,subprocess,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3'
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a42-cto-entrycopy3/reconstruction/pump-main/log_attempt.py'
MAIN=float(os.environ.get('MAIN','0.62672')); B=os.environ.get('B','53abf28')
done=set(open(O+'/recorded.txt').read().split()) if os.path.exists(O+'/recorded.txt') else set()
rows={}
for l in open(O+'/res.jsonl'):
    try: d=json.loads(l)
    except: continue
    if any(d.get('name','').startswith(p) for p in sys.argv[1:]): rows[d['name']]=d
for n,d in rows.items():
    if n in done: continue
    e=open(O+'/e/%s.py'%n).read().split('\n',1)[1].strip()
    r,b=d.get('ratio'),d.get('bytes')
    if r is None: st='compile-failed'
    elif b==27400 and r>MAIN: st='partial'
    elif r>MAIN: st='partial'
    else: st='rejected'
    note='raw-IR capture + rx opt/llc oracle (= build tokens) on main %s (0.62672). %s @%s B, eq_main=%s. %s'%(B,r,b,d.get('eq_main'),e)
    hyp='gene/size-knob screen on 53abf28 (genes30 g:, w13a34 knobs k:, w13a42 entry spellings x:): '+e
    data={'output':O+'/rx/'+n,'target':{'ratio':r,'slots_diff':d.get('slots_diff'),'cand_bytes':b},'notes':note}
    p=subprocess.run(['python3',L,'record','--lane','w13a42-cto-entrycopy3','--approach','entrycopy3-genescreen','--target','0x22a10',
      '--dedupe-key','0x22a10-w14-%s-entrycopy3-%s-v1'%(B,n),'--hypothesis',hyp,'--status',st,'--data',json.dumps(data)],capture_output=True,text=True)
    if p.returncode==0: done.add(n)
    else: print(n,p.stderr[-200:])
open(O+'/recorded.txt','w').write('\n'.join(sorted(done)))
print(len(done))
