#!/usr/bin/env python3
"""run.py <specfile> [workers]: each line 'name gene+gene+...' (or 'name -' for main). Builds via measure.sh, appends results.jsonl, records ledger."""
import sys,os,json,subprocess,shutil,threading,queue,glob
sys.path.insert(0,os.path.dirname(__file__)); import genes
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a64-cto-shiftpair')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a64-cto-shiftpair'
M='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh'
L=WT+'/reconstruction/pump-main/log_attempt.py'
BASESHA=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
SRCBASE=os.environ.get('SRCBASE',WT+'/programs/pump')
RES=OUT+f'/results-{BASESHA}.jsonl'
specs=[l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
nw=int(sys.argv[2]) if len(sys.argv)>2 else 2
done={json.loads(l)['name'] for l in open(RES)} if os.path.exists(RES) else set()
q=queue.Queue(); [q.put(s) for s in specs if s[0] not in done]
lock=threading.Lock()
def work(w):
    while True:
        try: name,gs=q.get_nowait()
        except queue.Empty: return
        gl=[] if gs=='-' else gs.split('+')
        v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
        subprocess.run(['rsync','-a','--exclude','target',SRCBASE+'/',v+'/'],check=True)
        f=v+'/src/creator/admin_cto.rs'
        try: s=genes.apply(open(f).read(),gl)
        except Exception as e:
            r={'name':name,'genes':gs,'error':'apply:'+repr(e)[:200]}
        else:
            open(f,'w').write(s)
            p=subprocess.run([M,v,f'{OUT}/work{w}',f'{OUT}/t/{name}'],capture_output=True,text=True)
            try: r=json.loads(p.stdout.strip().splitlines()[-1])
            except Exception: r={'ok':False,'error':p.stdout[-500:]+p.stderr[-500:]}
            if not r.get('ok') and ('BlockingIOError' in str(r.get('error','')) or 'temporarily unavailable' in str(r.get('error',''))):
                import time; time.sleep(20); shutil.rmtree(v,ignore_errors=True); q.put((name,gs)); continue
            r['name']=name; r['genes']=gs
        shutil.rmtree(v,ignore_errors=True)
        c=r.get('admin_cto') or {}
        line=f"{name:40s} {c.get('ratio')} {c.get('slots_diff')} {c.get('cand_bytes')} L{len(r.get('losses',[]) or [])}/{len(r.get('raw_losses',[]) or [])} {r.get('error','')[:80] if not r.get('ok') else ''}"
        with lock:
            open(RES,'a').write(json.dumps(r)+'\n'); print(line,flush=True)
        st='built' if r.get('ok') else 'compile-failed'
        if r.get('ok') and c.get('cand_bytes')==27400 and not r['losses'] and not r['raw_losses'] and c.get('ratio',0)>BEST: st='partial'
        elif r.get('ok'): st='rejected'
        data={'output':r.get('out',''),'normalized':r.get('normalized'),'raw':r.get('raw'),'losses':r.get('losses'),'raw_losses':r.get('raw_losses'),'target':{k:c.get(k) for k in ('ratio','slots_diff','cand_bytes')},'notes':f'shiftpair on main {BASESHA}: genes {gs}'}
        subprocess.run(['python3',L,'record','--lane','w14a64-cto-shiftpair','--approach','shiftpair','--target','0x22a10','--dedupe-key',f'0x22a10-w14-{BASESHA}-shiftpair-{name}-v1','--hypothesis',f'shiftpair trial on main {BASESHA}: {gs}','--status',st,'--data',json.dumps(data)],capture_output=True)
        # keep only json
        us=f'{OUT}/t/{name}/unstripped.so'
        if os.path.exists(us): subprocess.run(['python3',os.path.dirname(os.path.abspath(__file__))+'/tools/fnbin.py',us,f'{OUT}/t/{name}/fn.bin'],capture_output=True)
        for so in glob.glob(f'{OUT}/t/{name}/*.so'):
            if os.environ.get('KEEP')!='1': os.remove(so)
BEST=float(os.environ.get('BEST','0.65728'))
ts=[threading.Thread(target=work,args=(i,)) for i in range(nw)]; [t.start() for t in ts]; [t.join() for t in ts]
