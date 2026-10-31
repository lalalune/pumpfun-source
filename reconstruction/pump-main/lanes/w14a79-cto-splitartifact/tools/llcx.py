#!/usr/bin/env python3
"""llcx.py <name> <m.ll> [edits.py]: apply EDITS (exact (old,new) pairs or callables) to a post-opt slim module, run llc
like rx.py, write rx/<name>/fn.bin and print ratio/bytes/eq_main plus fmr L0/L1/L2 and per-0x800 L1 tokens. Experiment only."""
import sys, os, subprocess, runpy, json
D = os.path.dirname(os.path.abspath(__file__))
src = open(D + '/rx.py').read(); g = {'__name__': 'x'}; exec(src[:src.index("OUT=os.environ.get")], g)
OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact')
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
name, m = sys.argv[1], sys.argv[2]; t = open(m).read()
if len(sys.argv) > 3:
    for e in runpy.run_path(sys.argv[3])['EDITS']:
        if callable(e): t = e(t); continue
        x, y = e; c = t.count(x); assert c == 1, (c, x[:200]); t = t.replace(x, y)
d = OUT + '/rx/' + name; os.makedirs(d, exist_ok=True); open(d + '/m.ll', 'w').write(t)
r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
cand = g['elf_fn'](d + '/m.o', g['KEEP']); open(d + '/fn.bin', 'wb').write(cand)
rr, sd = g['metric'](cand, g['orig_window']())
bs = os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so')
res = {'name': name, 'ratio': round(rr, 5), 'bytes': len(cand), 'slots_diff': sd, 'eq_main': g['mask'](g['elf_fn'](bs, g['KEEP'])) == g['mask'](cand)}
print(json.dumps(res))
print(subprocess.run([sys.executable, D + '/fmr.py', d + '/fn.bin'], capture_output=True, text=True).stdout.strip())
