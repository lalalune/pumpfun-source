#!/usr/bin/env python3
"""vrun.py <queue> <results.jsonl> [workers]: build each gene spec with measure.sh; queue lines 'name' (gene spec)."""
import sys,os,json,subprocess,threading,time
M=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a25-cto-poollit')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a25-cto-poollit'
MS='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh'
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
            taken.add(p[0]); return p[0]
def work(w):
    while not os.path.exists(q+'.stop'):
        n=nxt()
        if not n:
            return
        r={'name':n}; ef=f'{M}/src_edits/{n}.py'; v=f'{M}/var/{n}'
        g=subprocess.run(['python3',M+'/e/gen.py',n,WT+'/programs/pump/src/creator/admin_cto.rs',ef],capture_output=True,text=True)
        if g.returncode: r['error']='gen:'+g.stderr[-300:]
        else:
            subprocess.run(['rm','-rf',v]); subprocess.run(['rsync','-a','--exclude','target',WT+'/programs/pump/',v+'/'])
            f=v+'/src/creator/admin_cto.rs'; s=open(f).read(); n0=s.count('\n'); G={}; exec(open(ef).read(),G)
            ok=True
            for a,b in G['EDITS']:
                if s.count(a)!=1: r['error']='edit-count'; ok=False; break
                s=s.replace(a,b)
            if ok and s.count('\n')!=n0: r['error']='newlines'; ok=False
            if ok:
                open(f,'w').write(s)
                o=f'{M}/t/{n}'
                c=subprocess.run(['bash',MS,v,f'{M}/work{w}',o],capture_output=True,text=True)
                try: r.update(json.loads(c.stdout.strip().split('\n')[-1]))
                except Exception: r['error']='measure:'+(c.stdout+c.stderr)[-300:]
                for x in ('candidate.so',):
                    pass
            subprocess.run(['rm','-rf',v])
        with lk: open(res,'a').write(json.dumps(r)+'\n')
ts=[threading.Thread(target=work,args=(i,)) for i in range(W)]
[t.start() for t in ts]; [t.join() for t in ts]
