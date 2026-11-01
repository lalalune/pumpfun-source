#!/usr/bin/env python3
"""orc.py IN.ll [--edit EDIT.py] [--name N] [--ref unstripped.so] : llc swap_hop, masked ratio vs original.
Edit file defines edit(text)->text applied to the extracted module."""
import sys, os, subprocess, difflib, runpy, struct, argparse, re, json, pickle
from pathlib import Path
H = './worktrees/w10r1-swaphop-slots/reconstruction/harness'
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O = Path(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-slots'))
ap = argparse.ArgumentParser(); ap.add_argument('ll'); ap.add_argument('--edit'); ap.add_argument('--name', default='x')
ap.add_argument('--ref'); ap.add_argument('--keep', action='store_true'); ap.add_argument('--dis', action='store_true')
ap.add_argument('--llc', default='')
a = ap.parse_args()
d = O / 'orc' / a.name; d.mkdir(parents=True, exist_ok=True)
t = open(a.ll).read()
if a.edit: t = runpy.run_path(a.edit)['edit'](t)
(d / 'm.ll').write_text(t)
r = subprocess.run([L + '/llc', '-O3', '-mtriple=sbf', '-mattr=+store-imm,+jmp-ext', '-relocation-model=pic', '-function-sections',
                    '-data-sections', '-filetype=obj', str(d / 'm.ll'), '-o', str(d / 'm.o')] + a.llc.split(), capture_output=True, text=True)
if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
secs = subprocess.run([L + '/llvm-objdump', '-h', str(d / 'm.o')], capture_output=True, text=True).stdout
sec = next(l.split()[1] for l in secs.splitlines() if 'multi_hop_curve8swap_hop17h' in l and '.rel' not in l)
subprocess.run([L + '/llvm-objcopy', '-O', 'binary', '--only-section=' + sec, str(d / 'm.o'), str(d / 'm.bin')], check=True)
raw = (d / 'm.bin').read_bytes()
P = O / 'orig_raw.bin'
if not P.exists():
    sys.path.insert(0, H); av = sys.argv; sys.argv = av[:1]
    import score; W = {x['start']: x for x in score.original_windows()}; P.write_bytes(W[0x5b3b0]['raw']); sys.argv = av
oraw = P.read_bytes()
def toks(raw):
    i = 0; out = []
    while i < len(raw):
        k = 16 if raw[i] == 0x18 else 8; x = bytearray(raw[i:i + k])
        if x[0] == 0x18: x[4:8] = bytes(4); x[12:16] = bytes(4)
        elif x[0] == 0x85: x[4:8] = bytes(4)
        out.append(bytes(x)); i += k
    return out
o = toks(oraw); c = toks(raw)
ratio = difflib.SequenceMatcher(None, o, c, autojunk=False).ratio()
opr = difflib.SequenceMatcher(None, [x[:2] for x in o], [x[:2] for x in c], autojunk=False).ratio()
res = {'name': a.name, 'bytes': len(raw), 'ratio': round(ratio, 5), 'opregs': round(opr, 5)}
if len(raw) == len(oraw): res['slots_diff'] = sum(1 for p, q in zip(o, c) if p != q)
if a.ref:
    sys.path.insert(0, H); from win import Cand
    cd = Cand(a.ref); s, n, nm = next(f for f in cd.funcs if re.search(r'multi_hop_curve8swap_hop17h', f[2]))
    res['ref_equal'] = toks(cd.fn(s, n)) == c; res['ref_bytes'] = n
print(json.dumps(res))
