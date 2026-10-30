#!/usr/bin/env python3
"""orc.py IN.ll [--edit EDIT.py] [--name N] [--show] [--opt] : (optionally opt -O3 a pre-opt module), extract swap_hop,
llc it, report bytes/ratio/slots vs original window 0x5b3b0. Edit file defines edit(text)->text."""
import sys, os, subprocess, difflib, runpy, argparse, re, json
from pathlib import Path
H = str(Path(__file__).resolve().parents[4] / 'harness')  # reconstruction/harness
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
HB = os.path.expanduser('~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin')
O = Path(os.environ.get('LANE_OUT', os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12b01-hop-gep')))
ap = argparse.ArgumentParser(); ap.add_argument('ll'); ap.add_argument('--edit'); ap.add_argument('--name', default='x')
ap.add_argument('--show', action='store_true'); ap.add_argument('--opt', action='store_true'); ap.add_argument('--llc', default='')
ap.add_argument('--optargs', default='')
a = ap.parse_args()
d = O / 'orc' / a.name; d.mkdir(parents=True, exist_ok=True)
src = a.ll
if a.edit:
    t = open(src).read(); t = runpy.run_path(a.edit)['edit'](t); (d / 'in.ll').write_text(t); src = str(d / 'in.ll')
if a.opt:
    r = subprocess.run([HB + '/opt', '-O3', '-mattr=+store-imm,+jmp-ext', src, '-S', '-o', str(d / 'opt.ll')] + a.optargs.split(), capture_output=True, text=True)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
    src = str(d / 'opt.ll')
subprocess.run(['python3', str(Path(__file__).resolve().parent / 'extract.py'), src, str(d / 'sh.ll'), 'multi_hop_curve8swap_hop17h'], check=True)
r = subprocess.run([L + '/llc', '-O3', '-mattr=+store-imm,+jmp-ext', '-relocation-model=pic', '-function-sections',
                    '-data-sections', '-filetype=obj', str(d / 'sh.ll'), '-o', str(d / 'm.o')] + a.llc.split(), capture_output=True, text=True)
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
res = {'name': a.name, 'bytes': len(raw), 'ratio': round(ratio, 5)}
if len(raw) == len(oraw):
    nb = lambda tk: b''.join(tk)
    no, nc = nb(o), nb(c)
    dif = [p for p in range(0, len(nc), 8) if no[p:p+8] != nc[p:p+8]]
    res['slots_diff'] = len(dif); res['first'] = [hex(p) for p in dif[:6]]
print(json.dumps(res))
if a.show:
    dis = subprocess.run([L + '/llvm-objdump', '-d', '--no-show-raw-insn', '-j', sec, str(d / 'm.o')], capture_output=True, text=True).stdout
    (d / 'dis.txt').write_text(dis)
