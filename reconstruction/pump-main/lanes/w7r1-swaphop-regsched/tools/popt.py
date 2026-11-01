#!/usr/bin/env python3
"""popt.py NAME EDIT.py [--base ir/noopt/module.ll]: edit pre-opt module, opt O3, extract swap_hop, llc oracle."""
import sys, os, subprocess, runpy, argparse
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-regsched')
B = '$HOME/Documents/Codex/2026-10-24/amm-sell-swarm/infra/sdk-native/rust/lib/rustlib/aarch64-apple-darwin/bin'
ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('edit'); ap.add_argument('--base', default=O + '/ir/noopt/module.ll')
a = ap.parse_args()
d = O + '/popt/' + a.name; os.makedirs(d, exist_ok=True)
t = open(a.base).read()
if a.edit != '-': t = runpy.run_path(a.edit)['edit'](t)
open(d + '/pre.ll', 'w').write(t)
r = subprocess.run([B + '/opt', '-passes=default<O3>', '-S', d + '/pre.ll', '-o', d + '/opt.ll'], capture_output=True, text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
subprocess.run([sys.executable, O + '/tools/extract.py', d + '/opt.ll', d + '/sh.ll'], check=True)
os.remove(d + '/pre.ll'); os.remove(d + '/opt.ll')
subprocess.run([sys.executable, O + '/tools/orc.py', d + '/sh.ll', '--name', 'p-' + a.name])
