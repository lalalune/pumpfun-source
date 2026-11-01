#!/usr/bin/env python3
"""step.py <name> [--mv58] [--noclimb] [--K 40] [--R 8]: price one union step (experiment only).
in: fx/<name>/m.ll (post-opt slim). --mv58 applies w17a21's MV58 post-opt block move first (s_nat1 shape).
out: st/<name>/{m.ll,fn.bin,step.json}: exact M/bytes (sdk llc), Mperm/Mhc (mp.py), tagged asm + votes (private llc),
     and with climb: the greedy sticky RA climb (climb.py) M and forces."""
import sys, os, json, subprocess, shutil
T = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(T); sys.path.insert(0, T)
import lx
a = sys.argv[1:]; name = a[0]
mv = '--mv58' in a; noclimb = '--noclimb' in a
K = int(a[a.index('--K') + 1]) if '--K' in a else 40
R = int(a[a.index('--R') + 1]) if '--R' in a else 8
src = a[a.index('--src') + 1] if '--src' in a else f'{OUT}/fx/{name}/m.ll'
d = f'{OUT}/st/{name}'; os.makedirs(d, exist_ok=True)
t = open(src).read()
if mv:
    import pipe
    t = pipe.MV58(t)
open(d + '/m.ll', 'w').write(t)
res = {'name': name, 'mv58': mv}
r = lx.run(d + '/m.ll', 'st_' + name, 'sdk')
if r.get('err'):
    res['err'] = r['err'][-300:]; print(json.dumps(res)); sys.exit(1)
shutil.copy2(f'{OUT}/lx/st_{name}/fn.bin', d + '/fn.bin')
res.update({k: r[k] for k in ('M', 'bytes', 'ratio', 'slots', 'eq_main', 'sig')})
q = subprocess.run(['python3', T + '/mp.py', 'st_' + name, d + '/m.ll'], capture_output=True, text=True)
try:
    j = json.loads(q.stdout.strip().splitlines()[-1]); res.update({k: j[k] for k in ('Mperm', 'Mhc') if k in j})
except Exception:
    res['mperr'] = (q.stdout[-200:] + q.stderr[-200:])
env = dict(os.environ, RAPRIO_TAG='1')
subprocess.run([T + '/llcp.sh', d + '/m.ll', '-o', d + '/tag.s'], env=env, capture_output=True)
v = subprocess.run(['python3', T + '/rvote.py', d + '/tag.s', d + '/fn.bin'], capture_output=True, text=True)
open(d + '/votes.jsonl', 'w').write(v.stdout)
res['nvotes'] = len(v.stdout.splitlines())
json.dump(res, open(d + '/step.json', 'w')); print(json.dumps(res), flush=True)
if not noclimb:
    c = subprocess.run(['python3', T + '/climb.py', d + '/m.ll', d + '/votes.jsonl', d + '/climb.jsonl', str(K), str(R)], capture_output=True, text=True)
    open(d + '/climb.log', 'w').write(c.stdout + c.stderr)
    fin = [json.loads(l) for l in c.stdout.splitlines() if l.startswith('{"final"')]
    if fin:
        res['climb'] = fin[0]['final']
    # best at exactly 27,400 B among all climb trials (sticky)
    rounds = [json.loads(l) for l in c.stdout.splitlines() if l.startswith('{"round"')]
    res['climb_rounds'] = [(x['round'], x['M'], x['bytes']) for x in rounds]
    json.dump(res, open(d + '/step.json', 'w')); print(json.dumps(res), flush=True)
