#!/usr/bin/env python3
"""q.py <res.jsonl> name...  : 2-worker capvar queue over e/<name>.py; appends rx results (with M) to res.jsonl"""
import sys,subprocess,threading,queue,json,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a31-cto-knob8')
res=sys.argv[1]; names=sys.argv[2:]; q=queue.Queue(); [q.put(n) for n in names]; lk=threading.Lock()
def w(slot):
    while True:
        try: n=q.get_nowait()
        except queue.Empty: return
        r=subprocess.run(['bash',OUT+'/tools/capvar.sh',n,OUT+'/e/'+n+'.py',str(slot)],capture_output=True,text=True,cwd=OUT)
        line=(r.stdout.strip().split('\n') or [''])[-1]
        try: d=json.loads(line)
        except Exception: d={'name':n,'error':(r.stdout+r.stderr)[-600:]}
        with lk:
            open(res,'a').write(json.dumps(d)+'\n'); print(json.dumps(d),flush=True)
        subprocess.run(['rm','-rf',OUT+'/var/'+n])
        try: os.remove(OUT+'/ir/'+n+'.ll')
        except OSError: pass
ts=[threading.Thread(target=w,args=(i,)) for i in (0,1)]; [t.start() for t in ts]; [t.join() for t in ts]
