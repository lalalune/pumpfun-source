#!/usr/bin/env python3
"""scr.py <specfile> [workers]: raw-IR oracle screen (experiment only).
Each spec line: 'name gene+gene+...' ('-' = main). Copies SRCBASE crate, applies genes (stitch12 library),
captures pre-opt IR (capraw.py identity build), runs rx.py (opt -O3 + llc), computes exact M, appends
res-<main7>.jsonl and records a ledger row. KEEPIR=1 keeps ir/<name>.ll."""
import sys,os,json,subprocess,shutil,threading,queue,difflib,time
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); genes=__import__(os.environ.get('GENES','genes_fu'))
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a09-cto-faithunion')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a09-cto-faithunion'
L=WT+'/reconstruction/pump-main/log_attempt.py'
BASESHA=os.environ.get('BASESHA') or open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
SRCBASE=os.environ.get('SRCBASE',WT+'/programs/pump')
TAG=os.environ.get('TAG',BASESHA)
RES=OUT+f'/res-{TAG}.jsonl'
from oracle import mask,orig_window
O=mask(orig_window()); MAINM=None
def Mof(fb):
    c=mask(open(fb,'rb').read()); return sum(b.size for b in difflib.SequenceMatcher(None,O,c,autojunk=False).get_matching_blocks())
specs=[l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
nw=int(sys.argv[2]) if len(sys.argv)>2 else 2
done={json.loads(l)['name'] for l in open(RES)} if os.path.exists(RES) else set()
q=queue.Queue(); [q.put(s[:2]) for s in specs if s[0] not in done]
lock=threading.Lock()
BM=int(os.environ.get('BM','2249'))
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
            cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True)
            import glob as _g
            for p in _g.glob(f'{OUT}/work{w}/target*/*/release/deps/pump_recovered*.ll'): os.remove(p)
            env=dict(os.environ,PUMP_BUILD_SLOTS='10')
            p=subprocess.run(['python3',T+'/capraw.py',v,f'{OUT}/work{w}',cap],capture_output=True,text=True,env=env)
            raw=cap+'/raw.ll'
            if not os.path.exists(raw):
                log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else p.stdout[-400:]+p.stderr[-400:]
                if 'BlockingIOError' in log or 'temporarily unavailable' in log or 'ENFILE' in log or 'Too many open files' in log or 'already in use' in log:
                    time.sleep(30); shutil.rmtree(v,ignore_errors=True); shutil.rmtree(cap,ignore_errors=True); q.put((name,gs)); continue
                i=log.find('error'); r={'name':name,'genes':gs,'error':'compile:'+log[i:i+300]}
            else:
                os.rename(raw,f'{OUT}/ir/{name}.ll'); shutil.rmtree(cap,ignore_errors=True)
                p=subprocess.run(['python3',T+'/rx.py',name,'--base',f'{OUT}/ir/{name}.ll'],capture_output=True,text=True,env=dict(os.environ,RX_OUT=OUT))
                try:
                    r=json.loads(p.stdout.strip().splitlines()[-1]); r['genes']=gs
                    r['M']=Mof(f'{OUT}/rx/{name}/fn.bin')
                    q2=subprocess.run(['python3',T+'/mp.py','mp_'+name,f'{OUT}/rx/{name}/m.ll'],capture_output=True,text=True)
                    mpj=json.loads(q2.stdout.strip().splitlines()[-1]); r.update({k:mpj[k] for k in ('Mperm','Mhc','lcs','lcs_hc','lcs_f') if k in mpj})
                    q3=subprocess.run(['python3',T+'/fuev.py',f'{OUT}/rx/{name}/fn.bin'],capture_output=True,text=True)
                    try:
                        fj=json.loads(q3.stdout.strip().splitlines()[-1]); r.update({k:fj[k] for k in ('L---','Lrfj','lcs_op','head_rfj','head_x','swap','dot')})
                    except Exception: pass
                except Exception: r={'name':name,'genes':gs,'error':'rx:'+(p.stdout[-300:]+p.stderr[-300:])}
                if os.environ.get('KEEPIR')!='1': os.remove(f'{OUT}/ir/{name}.ll')
                else: pass
                for x in ('m.o',):
                    try: os.remove(f'{OUT}/rx/{name}/{x}')
                    except OSError: pass
        shutil.rmtree(v,ignore_errors=True)
        r['secs']=round(time.time()-t0)
        with lock:
            open(RES,'a').write(json.dumps(r)+'\n')
            if 'error' in r: print(f"{name:28s} ERR {r['error'][:100]}",flush=True)
            else: print(f"{name:14s} {gs[:60]:60s} {r['bytes']:6d} {r['bytes']-27400:+5d} M {r['M']} {r['M']-BM:+d} Mp {r.get('Mperm')} Mhc {r.get('Mhc')} L--- {r.get('L---')} Lrfj {r.get('Lrfj')} op {r.get('lcs_op')} head {r.get('head_rfj')} swap {r.get('swap')} eq_main {r['eq_main']} {r['secs']}s",flush=True)
        st='compile-failed' if 'error' in r else 'analyzed'
        data={'output':f'{OUT}/rx/{name}','target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes'),'M':r.get('M'),'Mperm':r.get('Mperm'),'Mhc':r.get('Mhc'),'L---':r.get('L---'),'Lrfj':r.get('Lrfj'),'lcs_op':r.get('lcs_op'),'head_rfj':r.get('head_rfj'),'swap':r.get('swap')},
              'notes':f'faithunion raw-IR oracle (capraw+rx) on main {BASESHA}: genes {gs}; main M {BM}; eq_main {r.get("eq_main")}'+(' '+r.get('error','')[:120] if 'error' in r else '')}
        subprocess.run(['python3',L,'record','--lane','w16a09-cto-faithunion','--approach','faithunion','--target','0x22a10','--dedupe-key',f'0x22a10-w16-{BASESHA}-fu-{name}-v1','--hypothesis',f'faithunion raw-IR union capture on main {BASESHA}: {gs} (M, Mperm, Mhc, true LCS, head rfj, dotmap)','--status',st,'--data',json.dumps(data)],capture_output=True)
ts=[threading.Thread(target=work,args=(i,)) for i in range(nw)]; [t.start() for t in ts]; [t.join() for t in ts]
