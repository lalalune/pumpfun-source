#!/usr/bin/env python3
"""run.py <queue> <results.jsonl> [workers]: lines "name genespec" (genespec '+'-joined genes, or 'm').
Captures via capvar (slot = worker idx), scores ratio/bytes + fm/sk/es. Appends to results; skips names done. Stops on <queue>.stop."""
import sys,os,json,subprocess,threading,time
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a87-cto-skelunion2')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a87-cto-skelunion2'
q,res=sys.argv[1],sys.argv[2]; W=int(sys.argv[3]) if len(sys.argv)>3 else 2
lk=threading.Lock(); taken=set()
def done():
    s=set()
    if os.path.exists(res):
        for l in open(res):
            try: s.add(json.loads(l)['name'])
            except: pass
    return s
def nxt():
    with lk:
        d=done()
        for l in open(q):
            p=l.split()
            if not p or p[0].startswith('#') or p[0] in d or p[0] in taken: continue
            taken.add(p[0]); return p
def work(w):
    while not os.path.exists(q+'.stop'):
        p=nxt()
        if not p:
            if os.path.exists(q+'.drain'): return
            time.sleep(3); continue
        n,spec=p[0],p[1]; r={'name':n,'spec':spec}
        ef=f'{O}/src_edits/{n}.py'
        g=subprocess.run(['python3',O+'/e/gen.py',spec,WT+'/programs/pump/src/creator/admin_cto.rs',ef],capture_output=True,text=True)
        if g.returncode: r['error']='gen:'+g.stderr[-200:]
        else:
            c=subprocess.run(['bash',O+'/tools/capvar.sh',n,ef,str(w)],capture_output=True,text=True)
            try: r.update(json.loads(c.stdout.strip().split('\n')[-1]))
            except Exception: r['error']='cap:'+(c.stdout+c.stderr)[-300:]
            if False:
                e=subprocess.run(['python3',O+'/tools/ed.py',f'{O}/rx/{n}/m.ll','-',''],capture_output=True,text=True)
                try: d=json.loads(e.stdout); r.update(fm=d['fm'],sk=d['sk'],es=d['es'])
                except Exception: pass
            subprocess.run(['rm','-rf',f'{O}/var/{n}',f'{O}/ir/{n}.ll'])
            if os.path.exists(f'{O}/rx/{n}/m.o'): pass
        with lk: open(res,'a').write(json.dumps(r)+'\n')
ts=[threading.Thread(target=work,args=(i,)) for i in range(W)]
[t.start() for t in ts]; [t.join() for t in ts]
