#!/usr/bin/env python3
"""caldrive.py <varsmodule> <resfile> [names...]: capture each variant (2 build slots), then slim + full raw-IR oracle."""
import sys,os,json,subprocess,threading,queue,time,runpy
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.environ.get('LANE_OUT',os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a06-shim-irbeam')); sys.path.insert(0,T)
import fx
vm,resf=sys.argv[1],sys.argv[2]; V=runpy.run_path(vm)['V']
names=sys.argv[3:] or list(V)
done=set()
if os.path.exists(resf):
    for l in open(resf):
        try: done.add(json.loads(l)['name'])
        except Exception: pass
cq=queue.Queue(); [cq.put(n) for n in names if n not in done]
oq=queue.Queue(); lock=threading.Lock()
def capw(slot):
    while True:
        try: n=cq.get_nowait()
        except queue.Empty: return
        if not os.path.exists(f'{OUT}/ir/{n}.ll'):
            r=subprocess.run(['python3',T+'/capv.py',vm,n,str(slot)],capture_output=True,text=True)
            print(r.stdout.strip()[-200:],r.stderr.strip()[-300:],flush=True)
        if os.path.exists(f'{OUT}/ir/{n}.ll'): oq.put(n)
        else:
            with lock: open(resf,'a').write(json.dumps({'name':n,'err':open(f'{OUT}/ir/{n}.err').read()[-800:] if os.path.exists(f'{OUT}/ir/{n}.err') else 'capture failed'})+'\n')
def orw():
    while True:
        n=oq.get()
        if n is None: return
        res={'name':n}
        try:
            env=dict(os.environ,SURV=OUT+'/ir/surv2.txt')
            subprocess.run(['python3',T+'/preslim.py',f'{OUT}/ir/{n}.ll',f'{OUT}/ir/{n}.s.ll','keep'],env=env,capture_output=True)
            s=fx.run(open(f'{OUT}/ir/{n}.s.ll').read(),'s_'+n,keep=True)
            res['slim']={k:s.get(k) for k in ('M','bytes','ratio','err')}
            if os.environ.get('FULL')=='1':
                r=subprocess.run(['nice','-n','5','python3',T+'/rx.py',n,'--base',f'{OUT}/ir/{n}.ll'],capture_output=True,text=True)
                j=json.loads(r.stdout.strip().splitlines()[-1])
                b=open(f'{OUT}/rx/{n}/fn.bin','rb').read(); M,ratio=fx.Mof(b)
                res['full']={'M':M,'bytes':len(b),'ratio':round(ratio,5),'slots':j.get('slots_diff')}
        except Exception as e: res['err']=repr(e)[:300]
        with lock:
            open(resf,'a').write(json.dumps(res)+'\n'); print(json.dumps(res),flush=True)
caps=[threading.Thread(target=capw,args=(i,)) for i in range(2)]
ors=[threading.Thread(target=orw) for _ in range(2)]
[t.start() for t in caps+ors]; [t.join() for t in caps]
for _ in ors: oq.put(None)
[t.join() for t in ors]
