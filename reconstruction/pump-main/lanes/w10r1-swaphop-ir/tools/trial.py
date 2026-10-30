#!/usr/bin/env python3
"""trial.py NAME PATCH.py [--ir] [--score]: copy programs/pump to OUT/var/NAME, apply PATCH.py's
REPL = [(old,new),...] to src/multi_hop_curve_swap.rs (each old must occur once), build with fastbuild, print metric.
--ir also captures post-opt IR (for llc oracles)."""
import sys, os, subprocess, json, shutil, runpy, argparse
WT = '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w10r1-swaphop-ir'
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-ir')
H = WT + '/reconstruction/harness'; T = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('patch', nargs='*'); ap.add_argument('--ir', action='store_true')
ap.add_argument('--score', action='store_true'); ap.add_argument('--src', default=WT + '/programs/pump'); ap.add_argument('--work', default='work')
a = ap.parse_args()
d = f'{O}/var/{a.name}'
if os.path.exists(d): shutil.rmtree(d)
shutil.copytree(a.src, d + '/pump', ignore=shutil.ignore_patterns('target'))
f = d + '/pump/src/multi_hop_curve_swap.rs'; s = open(f).read()
for p in a.patch:
    for old, new in runpy.run_path(p)['REPL']:
        n = s.count(old)
        if n != 1: print(json.dumps({'name': a.name, 'error': f'patch {p}: count {n} for {old[:80]!r}'})); sys.exit(1)
        s = s.replace(old, new)
open(f, 'w').write(s)
env = dict(os.environ, PUMP_BUILD_SLOTS='10')
if a.ir:
    r = subprocess.run([sys.executable, T + '/capir.py', '--src', d + '/pump', '--work', f'{O}/irwork', '--out', d + '/out'], capture_output=True, text=True, env=env)
else:
    r = subprocess.run([sys.executable, H + '/fastbuild.py', '--src', d + '/pump', '--work', f'{O}/{a.work}', '--out', d + '/out'], capture_output=True, text=True, env=env)
so = d + '/out/unstripped.so'
if not os.path.exists(so):
    print(json.dumps({'name': a.name, 'error': 'build failed', 'log': (r.stdout + r.stderr)[-1500:]})); sys.exit(1)
m = json.loads(subprocess.run([sys.executable, H + '/target_metric.py', so, '0x5b3b0', '--sym', 'multi_hop_curve::swap_hop$', '--slots', '400'], capture_output=True, text=True).stdout)
res = {'name': a.name, 'bytes': m['cand_bytes'], 'ratio': m['ratio'], 'slots_diff': m.get('slots_diff'), 'calls': m['calls_candidate']}
if a.ir:
    subprocess.run([sys.executable, T + '/extract.py', d + '/out/module.ll', d + '/out/sh.ll'], check=True); os.remove(d + '/out/module.ll')
if a.score:
    sc = json.loads(subprocess.run([sys.executable, H + '/score.py', so, '--baseline', O + '/out/base/score.json', '--json', d + '/out/score.json', '--quiet'], capture_output=True, text=True).stdout)
    res.update(normalized=sc['normalized'], raw=sc['raw'], losses=sc['losses'], raw_losses=sc['raw_losses'], gains=sc['gains'], nraw_gains=len(sc['raw_gains']))
print(json.dumps(res))
