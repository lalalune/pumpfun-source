#!/usr/bin/env python3
"""r3run.py <genes.py> <set>... : build base admin_cto.rs + gene sets (exact newline-preserving substitutions, as in
w12a14 hc12.py) through measure.sh, 2 at a time; append ratio/bytes/losses + regcon region split to results.jsonl.
  set = comma-separated gene ids; env R3_PAR (2), R3_BASE (base .rs), R3_MAIN (sha7 tag)."""
import json,os,sys,subprocess,hashlib,importlib.util,threading,shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
LANE='w13a15-cto-region3of3'
SW=Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm'); WT=SW/'worktrees'/LANE
OUT=Path.home()/'.cache/pumpfun-reconstruction/lanes'/LANE
TOOLS=WT/'reconstruction/pump-main/lanes'/LANE/'tools'
BASE=Path(os.environ.get('R3_BASE',str(WT/'programs/pump/src/creator/admin_cto.rs')))
RES=OUT/'hc/results.jsonl'; MAIN=os.environ.get('R3_MAIN','7d7d9e5')
lock=threading.Lock(); workq=list(range(int(os.environ.get('R3_PAR','2'))))
def load(p):
    s=importlib.util.spec_from_file_location('g',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.GENES
def apply(t,G,ids):
    for g in ids:
        if not g: continue
        for o,n in G[g]:
            assert o.count('\n')==n.count('\n'),g
            c=t.count(o)
            if c!=1: raise ValueError(f'{g}: {c}x {o[:60]!r}')
            t=t.replace(o,n)
    return t
def regcon(so):
    r=subprocess.run(['python3',str(TOOLS/'regcon.py'),so],capture_output=True,text=True).stdout
    import re; return [int(x) for x in re.findall(r'M +(\d+)/',r)]
def build(G,label):
    ids=label.split(',')
    try: text=apply(BASE.read_text(),G,ids)
    except Exception as e:
        print(json.dumps({'label':label,'status':'apply-failed','err':str(e)[:200]}),flush=True); return
    vid=hashlib.sha256(text.encode()).hexdigest()[:12]
    with lock:
        if RES.exists() and any(json.loads(l).get('vid')==vid and json.loads(l).get('status')=='built' for l in RES.read_text().splitlines() if l.strip()):
            print('dup',label,flush=True); return
        w=workq.pop()
    try:
        var=OUT/'var'/vid; t=OUT/'t'/vid
        if var.exists(): shutil.rmtree(var)
        subprocess.run(['rsync','-a','--exclude','target',str(WT/'programs/pump')+'/',str(var)+'/'],check=True)
        (var/'src/creator/admin_cto.rs').write_text(text)
        p=subprocess.run([str(SW/'w11/tools/measure.sh'),str(var),str(OUT/f'work{w}'),str(t)],capture_output=True,text=True)
        line=(p.stdout.strip().splitlines() or ['{}'])[-1]
        try: d=json.loads(line)
        except Exception: d={'ok':False}
        r={'vid':vid,'label':label,'main':MAIN}
        if d.get('ok'):
            c=d['admin_cto']; r.update(status='built',bytes=c['cand_bytes'],ratio=c['ratio'],slots=c['slots_diff'],norm=d['normalized'],raw=d['raw'],
                losses=d['losses'],n_raw_losses=len(d['raw_losses']),sha=d['sha'],regions=regcon(str(t/'unstripped.so')),out=str(t))
        else: r.update(status='failed',err=str(d.get('error',''))[-300:])
        with lock:
            with open(RES,'a') as f: f.write(json.dumps(r)+'\n')
        print(json.dumps(r),flush=True)
        shutil.rmtree(var,ignore_errors=True)
        keep=r.get('status')=='built' and r['bytes']==27400 and not r['losses'] and r['n_raw_losses']==0 and r['ratio']>float(os.environ.get('R3_MAIN_RATIO','0.51228'))
        for f in (['link.map'] if keep else ['candidate.so','link.map']):
            try: (t/f).unlink()
            except Exception: pass
    finally:
        with lock: workq.append(w)
if __name__=='__main__':
    G=load(sys.argv[1]); sets=sys.argv[2:]
    if len(sets)==1 and sets[0].startswith('@'): sets=[l.strip() for l in open(sets[0][1:]) if l.strip()]
    with ThreadPoolExecutor(len(workq)) as ex: list(ex.map(lambda s:build(G,s),sets))
