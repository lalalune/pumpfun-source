#!/usr/bin/env python3
"""scr.py <names...> [-w N]: raw-IR oracle screen (experiment only). For each name, e/<name>.py holds EDITS (exact
(old,new) pairs on admin_cto.rs, line count kept). Copies the worktree crate, applies EDITS, captures pre-opt IR
(capraw.py, identity build), runs rx.py (opt -O3 + llc), then M / Mperm (relab) / TCF-clone marker.
Appends JSON rows to res.jsonl. KEEPIR=1 keeps ir/<name>.ll."""
import sys,os,json,subprocess,shutil,threading,queue,time,glob,runpy
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a07-cto-sweeptuple')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a07-cto-sweeptuple'
SRCBASE=os.environ.get('SRCBASE',WT+'/programs/pump')
RES=os.environ.get('RES',OUT+'/res.jsonl')
a=sys.argv[1:]; nw=2
if '-w' in a: i=a.index('-w'); nw=int(a[i+1]); del a[i:i+2]
q=queue.Queue(); [q.put(n) for n in a]
lock=threading.Lock()
import relab as R, marker as MK
ORIGM={'lam':'r7','key':'r9','data':'r0','E':'r5','own':'r6'}
def post(name):
    fb=f'{OUT}/rx/{name}/fn.bin'; b=open(fb,'rb').read()
    m0=R.M(b); sp=R.binspills(b); mb,pm=R.bestperm(b,sp,4)
    mk=MK.marker(b) or {}
    return {'M':m0,'Mperm':mb,'mk':{k:mk.get(k) for k in ('at','lam','key','data','E','own')},'mk_hits':sum(1 for k,v in ORIGM.items() if mk.get(k)==v)}
def work(w):
    while True:
        try: name=q.get_nowait()
        except queue.Empty: return
        v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
        subprocess.run(['rsync','-a','--exclude','target',SRCBASE+'/',v+'/'],check=True)
        f=v+'/src/creator/admin_cto.rs'; t0=time.time(); r=None
        try:
            s0=open(f).read(); s=s0
            for x,y in runpy.run_path(f'{OUT}/e/{name}.py')['EDITS']:
                c=s.count(x); assert c==1,(c,x[:100]); s=s.replace(x,y)
            if s.count('\n')!=s0.count('\n'): raise Exception('line count changed')
            open(f,'w').write(s)
        except Exception as e:
            r={'name':name,'error':'apply:'+repr(e)[:300]}
        if r is None:
            cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True)
            for p in glob.glob(f'{OUT}/work{w}/target*/*/release/deps/pump_recovered*.ll'): os.remove(p)
            env=dict(os.environ,PUMP_BUILD_SLOTS='10')
            p=subprocess.run(['python3',T+'/capraw.py',v,f'{OUT}/work{w}',cap],capture_output=True,text=True,env=env)
            raw=cap+'/raw.ll'
            if not os.path.exists(raw):
                log=''
                for lf in glob.glob(cap+'/*.log')+glob.glob(cap+'/*.err'): log+=open(lf,errors='replace').read()
                log+=p.stdout[-2000:]+p.stderr[-2000:]
                if any(k in log for k in ('BlockingIOError','temporarily unavailable','ENFILE','Too many open files','already in use','cannot lock')):
                    time.sleep(30); shutil.rmtree(v,ignore_errors=True); shutil.rmtree(cap,ignore_errors=True); q.put(name); continue
                i=log.find('error'); r={'name':name,'error':'compile:'+log[max(0,i):i+600]}
            else:
                os.rename(raw,f'{OUT}/ir/{name}.ll'); shutil.rmtree(cap,ignore_errors=True)
                p=subprocess.run(['python3',T+'/rx.py',name,'--base',f'{OUT}/ir/{name}.ll'],capture_output=True,text=True,env=dict(os.environ,RX_OUT=OUT))
                try:
                    r=json.loads(p.stdout.strip().splitlines()[-1]); r.update(post(name))
                except Exception as e: r={'name':name,'error':'rx:'+repr(e)[:200]+(p.stdout[-300:]+p.stderr[-300:])}
                if os.environ.get('KEEPIR')!='1': os.remove(f'{OUT}/ir/{name}.ll')
                mo=f'{OUT}/rx/{name}/m.o'
                if os.path.exists(mo): os.remove(mo)
        shutil.rmtree(v,ignore_errors=True)
        r['secs']=round(time.time()-t0,1)
        with lock:
            open(RES,'a').write(json.dumps(r)+'\n'); print(json.dumps(r),flush=True)
ts=[threading.Thread(target=work,args=(i,)) for i in range(nw)]
[t.start() for t in ts]; [t.join() for t in ts]
