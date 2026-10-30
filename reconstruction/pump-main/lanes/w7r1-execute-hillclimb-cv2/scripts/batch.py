#!/usr/bin/env python3
"""batch.py BASEFILE PREFIX MUTNAME... [--score] [--all]: apply each mutation (from muts.py) to BASEFILE, build 2 at a time."""
import sys, os, subprocess, threading, queue, json
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-hillclimb-cv2')
sys.path.insert(0,OUT+'/scripts'); import muts
args=sys.argv[1:]; score='--score' in args; args=[x for x in args if x!='--score']
base,prefix,names=args[0],args[1],args[2:]
if names==['ALL']: names=list(muts.M)
b=open(base).read(); q=queue.Queue()
for n in names:
    try: t=muts.apply(b,n.split('+'))
    except Exception as e: print(json.dumps({'name':n,'gen_error':str(e)[:200]}),flush=True); continue
    if t==b: print(json.dumps({'name':n,'gen_error':'noop'}),flush=True); continue
    nm=f'{prefix}-{n}'; p=f'{OUT}/v/{nm}.rs'; open(p,'w').write(t); q.put((nm,p))
def w(slot):
    while True:
        try: nm,p=q.get_nowait()
        except queue.Empty: return
        r=subprocess.run(['python3',OUT+'/scripts/trial.py',nm,p,'--slot',str(slot)]+(['--score'] if score else []),capture_output=True,text=True)
        print((r.stdout.strip().splitlines() or [r.stderr[-300:]])[-1],flush=True)
ts=[threading.Thread(target=w,args=(s,)) for s in (0,1)]; [t.start() for t in ts]; [t.join() for t in ts]
