#!/usr/bin/env python3
"""q.py <results.jsonl> name...: capture src_edits/<name>.py with 2 workers, append rx result + ch3 totals."""
import sys,os,json,subprocess,threading
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a58-cto-tafterlevy')
res=sys.argv[1]; names=sys.argv[2:]; lk=threading.Lock()
def work(w):
    while True:
        with lk:
            if not names: return
            n=names.pop(0)
        r={'name':n}
        c=subprocess.run(['bash',O+'/tools/capvar.sh',n,f'{O}/src_edits/{n}.py',str(w)],capture_output=True,text=True)
        try: r.update(json.loads(c.stdout.strip().split('\n')[-1]))
        except Exception: r['error']=(c.stdout+c.stderr)[-600:]
        subprocess.run(['rm','-rf',f'{O}/var/{n}',f'{O}/ir/{n}.ll'])
        with lk: open(res,'a').write(json.dumps(r)+'\n')
ts=[threading.Thread(target=work,args=(i,)) for i in range(2)]
[t.start() for t in ts]; [t.join() for t in ts]
