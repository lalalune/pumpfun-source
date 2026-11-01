#!/usr/bin/env python3
"""scr.py <specfile> [workers]: raw-IR oracle screen (experiment only), w16a05 copy of the w15a03/w15a16 screen.
Each spec line: 'name gene+gene+...' ('-' = main). Copies SRCBASE crate, applies genes (GENES module, default genes_mp),
captures pre-opt IR (capraw.py identity build, uses a build slot), runs rx.py (opt -O3 + llc), computes exact M and the
per-region profile vs main, appends res-<tag>.jsonl and records a ledger row (approach skelsplice)."""
import sys,os,json,subprocess,shutil,threading,queue,difflib,time,glob
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); genes=__import__(os.environ.get('GENES','genes_mp'))
sys.path.insert(0,os.path.join(os.path.dirname(T),'tools'))
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a05-cto-skelsplice')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a05-cto-skelsplice'
L=WT+'/reconstruction/pump-main/log_attempt.py'
BASESHA=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
SRCBASE=os.environ.get('SRCBASE',WT+'/programs/pump')
TAG=os.environ.get('TAG',BASESHA)
RES=OUT+f'/res-{TAG}.jsonl'
from oracle import mask,orig_window
O=mask(orig_window())
import regprof
from regs import R
import numpy as np
HR=regprof.hits('main')[0]
def prof(fb):
    h,_=regprof.hits(fb); OO=np.array(regprof.OO); out={}
    for lo,hi,n in R:
        m=(OO>=lo)&(OO<hi); d=int(h[m].sum()-HR[m].sum())
        if d: out[n]=d
    return int(h.sum()),out
specs=[l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
nw=int(sys.argv[2]) if len(sys.argv)>2 else 2
done={json.loads(l)['name'] for l in open(RES)} if os.path.exists(RES) else set()
q=queue.Queue(); [q.put(s[:2]) for s in specs if s[0] not in done]
lock=threading.Lock()
BM=2249
def work(w):
    while True:
        try: name,gs=q.get_nowait()
        except queue.Empty: return
        gl=[] if gs=='-' else gs.split('+')
        v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
        subprocess.run(['rsync','-a','--exclude','target',SRCBASE+'/',v+'/'],check=True)
        f=v+'/src/creator/admin_cto.rs'; t0=time.time()
        try:
            s0=open(f).read(); s=genes.apply(s0,gl)
            if s.count('\n')!=s0.count('\n'): raise Exception('line count changed')
        except Exception as e:
            r={'name':name,'genes':gs,'error':'apply:'+repr(e)[:200]}
        else:
            open(f,'w').write(s)
            cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True); os.makedirs(f'{OUT}/ir',exist_ok=True)
            for p in glob.glob(f'{OUT}/work{w}/target*/*/release/deps/pump_recovered*.ll'): os.remove(p)
            env=dict(os.environ,PUMP_BUILD_SLOTS='10')
            p=subprocess.run(['python3',T+'/capraw.py',v,f'{OUT}/work{w}',cap],capture_output=True,text=True,env=env)
            raw=cap+'/raw.ll'
            if not os.path.exists(raw):
                log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else p.stdout[-400:]+p.stderr[-400:]
                if any(x in log for x in ('BlockingIOError','temporarily unavailable','ENFILE','Too many open files','already in use')):
                    time.sleep(30); shutil.rmtree(v,ignore_errors=True); shutil.rmtree(cap,ignore_errors=True); q.put((name,gs)); continue
                i=log.find('error'); r={'name':name,'genes':gs,'error':'compile:'+log[i:i+300]}
            else:
                os.rename(raw,f'{OUT}/ir/{name}.ll'); shutil.rmtree(cap,ignore_errors=True)
                p=subprocess.run(['python3',T+'/rx.py',name,'--base',f'{OUT}/ir/{name}.ll'],capture_output=True,text=True)
                try:
                    r=json.loads(p.stdout.strip().splitlines()[-1]); r['genes']=gs
                    r['M'],r['dreg']=prof(f'{OUT}/rx/{name}/fn.bin')
                except Exception: r={'name':name,'genes':gs,'error':'rx:'+(p.stdout[-300:]+p.stderr[-300:])}
                if os.environ.get('KEEPIR')!='1': os.remove(f'{OUT}/ir/{name}.ll')
                try: os.remove(f'{OUT}/rx/{name}/m.o')
                except OSError: pass
        shutil.rmtree(v,ignore_errors=True)
        r['secs']=round(time.time()-t0)
        with lock:
            open(RES,'a').write(json.dumps(r)+'\n')
            if 'error' in r: print(f"{name:28s} ERR {r['error'][:100]}",flush=True)
            else: print(f"{name:28s} {r['bytes']:6d} {r['bytes']-27400:+5d} M {r['M']} {r['M']-BM:+d} slots {r['slots_diff']} eq_main {r['eq_main']} {r['secs']}s {r['dreg']}",flush=True)
        st='compile-failed' if 'error' in r else 'analyzed'
        data={'output':f'{OUT}/rx/{name}','target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes'),'M':r.get('M')},
              'notes':f'skelsplice raw-IR oracle (capraw+rx) on main {BASESHA}: genes {gs}; main M {BM}; eq_main {r.get("eq_main")}; region dM {r.get("dreg")}'+(' '+r.get('error','')[:120] if 'error' in r else '')}
        subprocess.run(['python3',L,'record','--lane','w16a05-cto-skelsplice','--approach','skelsplice','--target','0x22a10','--dedupe-key',f'0x22a10-w16-{BASESHA}-skelsplice-{name}-v1','--hypothesis',f'skelsplice composite screen on main {BASESHA}: {gs}','--status',st,'--data',json.dumps(data)],capture_output=True)
ts=[threading.Thread(target=work,args=(i,)) for i in range(nw)]; [t.start() for t in ts]; [t.join() for t in ts]
