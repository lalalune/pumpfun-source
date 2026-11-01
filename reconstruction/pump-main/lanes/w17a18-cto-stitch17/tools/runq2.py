#!/usr/bin/env python3
"""runq2.py <queue file> [workers=2] [slot0]: dynamic queue (re-read each pop; lines 'name genes'); skips names in res/cap.jsonl
or in progress; stops when the queue has no runnable line for 10 minutes or file STOP exists."""
import sys,os,subprocess,threading,json,time
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
qf=sys.argv[1]; W=int(sys.argv[2]) if len(sys.argv)>2 else 2; S0=int(sys.argv[3]) if len(sys.argv)>3 else 0
lock=threading.Lock(); running=set()
def done():
    d=set()
    if os.path.exists(OUT+'/res/cap.jsonl'):
        for l in open(OUT+'/res/cap.jsonl'):
            try: d.add(json.loads(l)['name'])
            except Exception: pass
    return d
def pop():
    with lock:
        d=done()
        for l in open(qf):
            l=l.strip()
            if not l or l.startswith('#'): continue
            p=l.split(); n=p[0]; g=p[1] if len(p)>1 else ''
            if n in d or n in running: continue
            running.add(n); return n,g
    return None
def work(slot):
    idle=0
    while not os.path.exists(OUT+'/STOP'):
        j=pop()
        if j is None:
            time.sleep(5); idle+=5
            if idle>600: return
            continue
        idle=0; n,g=j
        subprocess.run(['python3',T+'/cap.py',n,g,str(slot)],stdout=subprocess.DEVNULL,stderr=open(f'{OUT}/ir/err_{n}.txt','w'))
        e=f'{OUT}/ir/err_{n}.txt'
        if os.path.exists(e) and os.path.getsize(e)==0: os.remove(e)
        with lock: running.discard(n)
ts=[threading.Thread(target=work,args=(S0+i,)) for i in range(W)]
[t.start() for t in ts]; [t.join() for t in ts]
print('done')
