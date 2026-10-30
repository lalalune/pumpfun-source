#!/usr/bin/env python3
"""rec.py <results.jsonl> <hyp map json> : record unrecorded rows to the ledger"""
import sys,json,subprocess,os
M=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a25-cto-poollit')
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a25-cto-poollit/reconstruction/pump-main/log_attempt.py'
H=json.load(open(sys.argv[2])); base=sys.argv[3] if len(sys.argv)>3 else '1b0ae70'
MAIN=float(os.environ.get('MAINR','0.6414'))
dn=set(open(M+'/recorded.txt').read().split()) if os.path.exists(M+'/recorded.txt') else set()
for l in open(sys.argv[1]):
    r=json.loads(l); n=r['name']
    if n in dn: continue
    c=r.get('admin_cto',{}); k=f'0x22a10-w14-{base}-poollit-{n}-v1'
    if 'error' in r: st='compile-failed'
    elif r.get('sha')==os.environ.get('MAINSHA','37ce7ef91dc484d5'): st='rejected'
    elif c.get('ratio',0)>MAIN and c.get('cand_bytes')==27400 and not r.get('losses') and not r.get('raw_losses'): st='partial'
    else: st='rejected'
    note=('byte-identical to main; ' if r.get('sha')==os.environ.get('MAINSHA','37ce7ef91dc484d5') else '')+f"calls {c.get('calls_candidate')}; measure.sh build"
    d={'output':r.get('out',''),'normalized':r.get('normalized'),'raw':r.get('raw'),'losses':r.get('losses',[]),'raw_losses':r.get('raw_losses',[]),'target':{'ratio':c.get('ratio'),'slots_diff':c.get('slots_diff'),'cand_bytes':c.get('cand_bytes')},'notes':note+(' '+r.get('error','')[:200] if 'error' in r else '')}
    p=subprocess.run(['python3',L,'record','--lane','w14a25-cto-poollit','--approach','poollit','--target','0x22a10','--dedupe-key',k,'--hypothesis',H.get(n,n),'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    print(n,st,p.returncode,p.stderr[-200:])
    open(M+'/recorded.txt','a').write(n+'\n')
