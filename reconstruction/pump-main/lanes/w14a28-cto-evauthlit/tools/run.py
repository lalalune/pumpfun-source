#!/usr/bin/env python3
"""run.py <res.jsonl> <name>...: build each variant from e/var.py with measure.sh, 2 workers."""
import sys,os,json,subprocess,threading
M=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a28-cto-evauthlit')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a28-cto-evauthlit'
D=WT+'/reconstruction/pump-main/lanes/w14a28-cto-evauthlit'
MS='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh'
G={}; exec(open(D+'/e/var.py').read(),G); V=G['V']
res=sys.argv[1]; names=sys.argv[2:]; lk=threading.Lock(); W=int(os.environ.get('W','2'))
def work(w):
    while True:
        with lk:
            if not names: return
            n=names.pop(0)
        r={'name':n}; v=f'{M}/var/{n}'
        subprocess.run(['rm','-rf',v]); subprocess.run(['rsync','-a','--exclude','target',WT+'/programs/pump/',v+'/'])
        f=v+'/src/creator/admin_cto.rs'; s=open(f).read(); n0=s.count('\n'); ok=True
        for a,b in V[n]:
            if s.count(a)!=1: r['error']='edit-count:'+a[:60]; ok=False; break
            s=s.replace(a,b)
        if ok and s.count('\n')!=n0: r['error']='newlines'; ok=False
        if ok:
            open(f,'w').write(s)
            c=subprocess.run(['bash',MS,v,f'{M}/work{w}',f'{M}/t/{n}'],capture_output=True,text=True)
            try: r.update(json.loads(c.stdout.strip().split('\n')[-1]))
            except Exception: r['error']='measure:'+(c.stdout+c.stderr)[-300:]
        subprocess.run(['rm','-rf',v])
        a=r.get('admin_cto',{})
        print(n,r.get('sha','')[:16],a.get('ratio'),a.get('slots_diff'),a.get('cand_bytes'),a.get('calls_candidate'),len(r.get('losses',[])),len(r.get('raw_losses',[])),r.get('error','')[:200],flush=True)
        with lk: open(res,'a').write(json.dumps(r)+'\n')
ts=[threading.Thread(target=work,args=(i,)) for i in range(W)]
[t.start() for t in ts]; [t.join() for t in ts]
