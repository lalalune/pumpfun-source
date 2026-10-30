#!/usr/bin/env python3
"""qd.py <queue.txt> <results.jsonl>: 2 workers; re-reads queue each pop (edit it live); skips names already in results; stop with <queue>.stop."""
import sys,os,json,subprocess,threading,time
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
q,res=sys.argv[1],sys.argv[2]; lk=threading.Lock(); taken=set()
def nxt():
    with lk:
        d=set()
        if os.path.exists(res):
            for l in open(res):
                try: d.add(json.loads(l)['name'])
                except: pass
        for l in open(q):
            n=l.strip()
            if n and not n.startswith('#') and n not in d and n not in taken: taken.add(n); return n
def work(w):
    while not os.path.exists(q+'.stop'):
        n=nxt()
        if not n: time.sleep(5); continue
        r={'name':n}
        c=subprocess.run(['bash',O+'/tools/capvar.sh',n,f'{O}/src_edits/{n}.py',str(w)],capture_output=True,text=True)
        try: r.update(json.loads(c.stdout.strip().split('\n')[-1]))
        except Exception: r['error']=(c.stdout+c.stderr)[-600:]
        subprocess.run(['rm','-rf',f'{O}/var/{n}',f'{O}/ir/{n}.ll'])
        with lk: open(res,'a').write(json.dumps(r)+'\n')
ts=[threading.Thread(target=work,args=(i,)) for i in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
