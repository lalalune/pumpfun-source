#!/usr/bin/env python3
"""trial.py NAME FILE.rs [--slot N] [--score]: copy FILE.rs to src-N/src/create_v2.rs, fastbuild, target_metric 0x1e7c0, optional score."""
import sys, os, json, subprocess, shutil, argparse, time, hashlib
from pathlib import Path
L='w7r1-execute-hillclimb-cv2'
OUT = Path.home()/f'.cache/pumpfun-reconstruction/lanes/{L}'
WT = Path(f'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/{L}')
H = WT/'reconstruction/harness'
os.environ['PUMP_BUILD_SLOTS']='10'
ap=argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('file'); ap.add_argument('--slot',default='0'); ap.add_argument('--score',action='store_true')
a=ap.parse_args()
src=OUT/f'src-{a.slot}'; work=OUT/f'work-{a.slot}'; out=OUT/'trials'/a.name
out.mkdir(parents=True,exist_ok=True)
shutil.copy2(a.file,src/'src/create_v2.rs'); shutil.copy2(a.file,out/'create_v2.rs')
res={'name':a.name}
for att in range(6):
    p=subprocess.run(['python3',str(H/'fastbuild.py'),'--src',str(src),'--work',str(work),'--out',str(out)],capture_output=True,text=True)
    if p.returncode==0 and (out/'unstripped.so').exists(): res['ok']=True; break
    log=p.stdout+p.stderr
    if 'Too many open files' in log or 'ENFILE' in log: time.sleep(60); continue
    res['ok']=False; errs=[l for l in log.splitlines() if 'error' in l.lower()][:4]; res['error']=errs or log[-400:]; break
if res.get('ok'):
    m=subprocess.run(['python3',str(H/'target_metric.py'),str(out/'unstripped.so'),'0x1e7c0','--sym','create_v2::execute$','--top','1'],capture_output=True,text=True).stdout
    try:
        tm=json.loads(m.splitlines()[0]); res.update(ratio=tm['ratio'],bytes=tm['cand_bytes'],calls=tm['calls_candidate'],norm=tm['normalized_equal'],raw=tm['raw_equal'])
    except Exception: res['metric_error']=m[-300:]
    res['sha']=hashlib.sha256((out/'unstripped.so').read_bytes()).hexdigest()[:12]
    if a.score:
        s=subprocess.run(['python3',str(H/'score.py'),str(out/'unstripped.so'),'--baseline',str(OUT/'out/base/score.json'),'--json',str(out/'score.json'),'--quiet'],capture_output=True,text=True).stdout
        try:
            sj=json.loads(s.strip().splitlines()[-1]); res.update(N=sj['normalized'],R=sj['raw'],gains=sj['gains'],losses=sj['losses'],rgains=len(sj['raw_gains']),rlosses=sj['raw_losses'])
        except Exception: res['score_error']=s[-300:]
    (out/'candidate.so').unlink(missing_ok=True)
line=json.dumps(res)
with open(OUT/'results.jsonl','a') as fh: fh.write(line+'\n')
print(line,flush=True)
