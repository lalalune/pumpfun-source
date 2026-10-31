#!/usr/bin/env python3
"""scr.py <specfile> [workers]: literal-order raw-IR screen (experiment only).
Spec line: 'name key:order[;key:order...]' ('-' = main). order = hex digits of field indices.
Copies the worktree crate, permutes literals, captures pre-opt IR (capraw identity build), runs rx.py,
computes M, appends res-<sha7>.jsonl and records a ledger row (approach litfamily)."""
import sys,os,json,subprocess,shutil,threading,queue,difflib,time,glob
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import lit
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a30-cto-litfamily')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a30-cto-litfamily'
L=WT+'/reconstruction/pump-main/log_attempt.py'
SHA=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA')).read().strip()[:7]
SRCBASE=os.environ.get('SRCBASE',WT+'/programs/pump')
RES=OUT+f'/res-{SHA}.jsonl'
exec(open(T+'/rx.py').read().split('OUT=os.environ')[0])
O=mask(orig_window())
def Mof(fb):
    c=mask(open(fb,'rb').read()); return sum(b.size for b in difflib.SequenceMatcher(None,O,c,autojunk=False).get_matching_blocks())
specs=[l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
nw=int(sys.argv[2]) if len(sys.argv)>2 else 2
done={json.loads(l)['name'] for l in open(RES)} if os.path.exists(RES) else set()
q=queue.Queue(); [q.put(s[:2]) for s in specs if s[0] not in done]
lock=threading.Lock(); BM=int(os.environ.get('BM','2249'))
REPS=json.load(open(T+'/reps.json')) if os.path.exists(T+'/reps.json') else {}
def edit(s,gs):
    if gs=='-': return s
    for part in gs.split(';'):
        k,o=part.split(':')
        if k=='R':
            for x,y in REPS[o]:
                assert s.count(x)==1,(o,x[:80]); s=s.replace(x,y)
            continue
        s=lit.permute(s,k,[int(c,16) for c in o])
    return s
def work(w):
    while True:
        try: name,gs=q.get_nowait()
        except queue.Empty: return
        v=f'{OUT}/var/{name}'; shutil.rmtree(v,ignore_errors=True)
        subprocess.run(['rsync','-a','--exclude','target',SRCBASE+'/',v+'/'],check=True)
        f=v+'/src/creator/admin_cto.rs'; t0=time.time()
        s0=open(f).read(); s=edit(s0,gs); assert s.count('\n')==s0.count('\n')
        open(f,'w').write(s)
        cap=f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap,ignore_errors=True)
        for p in glob.glob(f'{OUT}/work{w}/target*/*/release/deps/pump_recovered*.ll'): os.remove(p)
        p=subprocess.run(['python3',T+'/capraw.py',v,f'{OUT}/work{w}',cap],capture_output=True,text=True,env=dict(os.environ,PUMP_BUILD_SLOTS='10'))
        raw=cap+'/raw.ll'
        if not os.path.exists(raw):
            log=open(cap+'/build.log').read() if os.path.exists(cap+'/build.log') else p.stdout[-400:]+p.stderr[-400:]
            if any(x in log for x in ('BlockingIOError','temporarily unavailable','ENFILE','Too many open files','already in use')):
                time.sleep(30); shutil.rmtree(v,ignore_errors=True); shutil.rmtree(cap,ignore_errors=True); q.put((name,gs)); continue
            i=log.find('error'); r={'name':name,'genes':gs,'error':'compile:'+log[i:i+300]}
        else:
            os.rename(raw,f'{OUT}/ir/{name}.ll'); shutil.rmtree(cap,ignore_errors=True)
            p=subprocess.run(['python3',T+'/rx.py',name,'--base',f'{OUT}/ir/{name}.ll'],capture_output=True,text=True,env=dict(os.environ,RX_OUT=OUT))
            try:
                r=json.loads(p.stdout.strip().splitlines()[-1]); r['genes']=gs; r['M']=Mof(f'{OUT}/rx/{name}/fn.bin')
            except Exception: r={'name':name,'genes':gs,'error':'rx:'+(p.stdout[-300:]+p.stderr[-300:])}
            if os.environ.get('KEEPIR')!='1': os.remove(f'{OUT}/ir/{name}.ll')
            try: os.remove(f'{OUT}/rx/{name}/m.o')
            except OSError: pass
        shutil.rmtree(v,ignore_errors=True); r['secs']=round(time.time()-t0)
        with lock:
            open(RES,'a').write(json.dumps(r)+'\n')
            if 'error' in r: print(f"{name:24s} ERR {r['error'][:100]}",flush=True)
            else: print(f"{name:24s} {r['bytes']:6d} {r['bytes']-27400:+5d} M {r['M']} {r['M']-BM:+d} slots {r['slots_diff']} eq_main {r['eq_main']} {r['secs']}s",flush=True)
        st='compile-failed' if 'error' in r else 'analyzed'
        data={'output':f'{OUT}/rx/{name}','target':{'ratio':r.get('ratio'),'slots_diff':r.get('slots_diff'),'cand_bytes':r.get('bytes'),'M':r.get('M')},
              'notes':f'litfamily raw-IR oracle (capraw+rx) on main {SHA}: literal init order {gs}; main M {BM}; eq_main {r.get("eq_main")}'+(' '+r.get('error','')[:120] if 'error' in r else '')}
        subprocess.run(['python3',L,'record','--lane','w15a30-cto-litfamily','--approach','litfamily','--target','0x22a10','--dedupe-key',f'0x22a10-w15-{SHA}-litfamily-{name}-v1','--hypothesis',f'literal field init-order screen on main {SHA}: {gs}','--status',st,'--data',json.dumps(data)],capture_output=True)
ts=[threading.Thread(target=work,args=(i,)) for i in range(nw)]; [t.start() for t in ts]; [t.join() for t in ts]
