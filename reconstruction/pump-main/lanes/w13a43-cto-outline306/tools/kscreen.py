#!/usr/bin/env python3
# kscreen.py <base var> <prefix> <results.jsonl> [knob ...]: apply each sizeknob (sizeknobs-cto.json) on var/<base>,
# run src.sh two at a time, append {knob, ratio, bytes, lddw, outl, masked} to results; deletes the var copy + IR after.
import sys,json,os,subprocess,re,shutil
from concurrent.futures import ThreadPoolExecutor
import queue
WQ=queue.Queue(); WQ.put('work0'); WQ.put('work1')
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w13a43-cto-outline306'); T=O+'/tools'
base,pre,res=sys.argv[1:4]; only=sys.argv[4:]
K=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']
src=open(f'{O}/var/{base}/src/creator/admin_cto.rs').read()
jobs=[]
for k in K:
    ed=k.get('edit') or k.get('edits') or []
    if not ed or (only and k['name'] not in only): continue
    if all(src.count(e['old'])==1 for e in ed): jobs.append((k['name'],ed))
print(len(jobs),'applicable',flush=True)
def run(i_job):
    i,(n,ed)=i_job; v=f'{pre}_{n}'; d=f'{O}/var/{v}'
    if not os.path.exists(d): subprocess.run(['rsync','-a',f'{O}/var/{base}/',d+'/'],check=True)
    p=d+'/src/creator/admin_cto.rs'; s=src
    for e in ed: s=s.replace(e['old'],e['new'])
    open(p,'w').write(s)
    w=WQ.get()
    try: r=subprocess.run([T+'/src.sh',v,w],capture_output=True,text=True).stdout
    finally: WQ.put(w)
    m=re.search(r'ratio (\S+) insns \S+ \S+ bytes (\d+) lddw (\d+)',r); rec={'knob':n,'var':v}
    if m:
        rec.update(ratio=float(m.group(1)),bytes=int(m.group(2)),lddw=int(m.group(3)))
        rec['outl']=subprocess.run(['python3',T+'/tsites.py',f'{O}/x/{v}'],capture_output=True,text=True).stdout.split(':',1)[-1].strip()
        rec['masked']=subprocess.run(['python3',T+'/mratio2.py',O+'/orig_fn.txt',f'{O}/x/{v}/fn.txt'],capture_output=True,text=True).stdout.strip()
    else: rec['err']=r[-300:]
    with open(res,'a') as f: f.write(json.dumps(rec)+'\n')
    print(json.dumps(rec),flush=True)
    shutil.rmtree(f'{O}/ir/{v}',ignore_errors=True)
with ThreadPoolExecutor(2) as ex: list(ex.map(run,enumerate(jobs)))
