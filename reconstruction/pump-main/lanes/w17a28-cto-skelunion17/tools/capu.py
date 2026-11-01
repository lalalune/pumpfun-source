#!/usr/bin/env python3
"""capu.py <name> <slot> <GENE+GENE+...>: copy the lane crate, apply genes.py genes in order (line count kept),
capture pre-opt IR (capraw), preslim, fx score. Writes ir/<name>.slim.ll and fx/<name>/{m.ll,fn.bin}. Experiment only."""
import sys, os, runpy, subprocess, shutil, glob, time, json
T = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(T)
WT = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a28-cto-skelunion17'
name, slot, combo = sys.argv[1], sys.argv[2], sys.argv[3]
G = runpy.run_path(T + '/genes.py')['G']
src = os.environ.get('SRCB', WT + '/programs/pump')
v = f'{OUT}/var/{name}'; shutil.rmtree(v, ignore_errors=True)
subprocess.run(['rsync', '-a', '--exclude', 'target', src + '/', v + '/'], check=True)
p = v + '/src/creator/admin_cto.rs'; s = open(p).read(); n0 = s.count('\n')
ORDER=['K8','NAT','N1','VE','S3','OL','OLb','FO','FOp','HL','HL2','VHL']
for g in sorted([x for x in combo.split('+') if x and x != 'm'],key=ORDER.index):
    for f in G[g]:
        s = f(s)
assert s.count('\n') == n0, (name, 'line count changed')
open(p, 'w').write(s)
os.makedirs(f'{OUT}/src', exist_ok=True); shutil.copy2(p, f'{OUT}/src/{name}.rs')
w = f'{OUT}/work{slot}'; os.makedirs(w, exist_ok=True)
for q in glob.glob(w + '/target*/*/release/deps/pump_recovered*.ll'):
    os.remove(q)
cap = f'{OUT}/ir/cap_{name}'; shutil.rmtree(cap, ignore_errors=True); t0 = time.time()
for attempt in range(3):
    r = subprocess.run(['python3', T + '/capraw.py', v, w, cap], capture_output=True, text=True, env=dict(os.environ, PUMP_BUILD_SLOTS='10'))
    if os.path.exists(cap + '/raw.ll'):
        break
    log = r.stdout[-3000:] + r.stderr[-3000:]
    if any(k in log for k in ('ENFILE', 'Too many open files', 'temporarily unavailable', 'cannot lock ref')):
        time.sleep(20); continue
    break
if not os.path.exists(cap + '/raw.ll'):
    open(f'{OUT}/ir/{name}.err', 'w').write(r.stdout[-4000:] + r.stderr[-4000:])
    print(json.dumps({'name': name, 'combo': combo, 'err': 'capture failed'}), flush=True)
    shutil.rmtree(v, ignore_errors=True); sys.exit(1)
raw = f'{OUT}/ir/{name}.raw.ll'; os.rename(cap + '/raw.ll', raw); shutil.rmtree(cap, ignore_errors=True); shutil.rmtree(v, ignore_errors=True)
slim = f'{OUT}/ir/{name}.slim.ll'
subprocess.run(['python3', T + '/preslim.py', raw, slim, 'keep'], env=dict(os.environ, SURV=T + '/surv-1647da0.txt'), capture_output=True, check=True)
os.remove(raw)
r = subprocess.run(['python3', T + '/fx.py', slim, name], env=dict(os.environ, LANE_OUT=OUT), capture_output=True, text=True)
res = json.loads(r.stdout.strip().splitlines()[-1]); res['combo'] = combo; res['cap_s'] = round(time.time() - t0)
print(json.dumps(res), flush=True)
