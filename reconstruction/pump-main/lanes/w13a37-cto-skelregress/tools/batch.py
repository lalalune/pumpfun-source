#!/usr/bin/env python3
"""batch.py <list.jsonl> [jobs]: each line {"name":..,"spec":{..}}; runs run.sh with N parallel work slots, skipping names already in results."""
import sys,json,subprocess,threading,queue,os
OUT='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a37-cto-skelregress'
items=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
J=int(sys.argv[2]) if len(sys.argv)>2 else 2
done=set()
if os.path.exists(OUT+'/results.jsonl'):
    for l in open(OUT+'/results.jsonl'):
        try: done.add(json.loads(l)['name'])
        except Exception: pass
q=queue.Queue()
for it in items:
    if it['name'] not in done: q.put(it)
def w(slot):
    while True:
        try: it=q.get_nowait()
        except queue.Empty: return
        subprocess.run([OUT+'/tools/run.sh',it['name'],json.dumps(it['spec']),str(slot)])
ts=[threading.Thread(target=w,args=(i,)) for i in range(J)]
[t.start() for t in ts]; [t.join() for t in ts]
print('batch done')
