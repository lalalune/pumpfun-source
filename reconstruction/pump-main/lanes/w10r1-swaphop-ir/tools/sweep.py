#!/usr/bin/env python3
# sweep.py IN.ll TAG kinds [-j N]: run all single mutations through llc, rank by ratio
import sys, os, json, subprocess, difflib, concurrent.futures as cf, tempfile
sys.path.insert(0, os.path.dirname(__file__)); import mut
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-ir')
src, tag, kinds = sys.argv[1:4]; J = int(sys.argv[5]) if len(sys.argv) > 5 else 4
t = open(src).read(); pre, hdr, blocks, post, ms = mut.muts(t, kinds.split(','))
print(len(ms), 'mutations', file=sys.stderr)
oraw = open(O + '/orig_raw.bin', 'rb').read()
def toks(raw):
    i = 0; out = []
    while i < len(raw):
        k = 16 if raw[i] == 0x18 else 8; x = bytearray(raw[i:i + k])
        if x[0] == 0x18: x[4:8] = bytes(4); x[12:16] = bytes(4)
        elif x[0] == 0x85: x[4:8] = bytes(4)
        out.append(bytes(x)); i += k
    return out
OT = toks(oraw)
def run(m):
    d = tempfile.mkdtemp(dir=O + '/tmp')
    try:
        open(d + '/m.ll', 'w').write(mut.apply(pre, hdr, blocks, post, m))
        r = subprocess.run([L + '/llc', '-O3', '-mtriple=sbf', '-mattr=+store-imm,+jmp-ext', '-relocation-model=pic', '-function-sections', '-filetype=obj', d + '/m.ll', '-o', d + '/m.o'], capture_output=True, text=True)
        if r.returncode: return (m[0], None, None)
        secs = subprocess.run([L + '/llvm-objdump', '-h', d + '/m.o'], capture_output=True, text=True).stdout
        sec = next(l.split()[1] for l in secs.splitlines() if 'multi_hop_curve8swap_hop17h' in l and '.rel' not in l)
        subprocess.run([L + '/llvm-objcopy', '-O', 'binary', '--only-section=' + sec, d + '/m.o', d + '/m.bin'], check=True)
        raw = open(d + '/m.bin', 'rb').read()
        return (m[0], round(difflib.SequenceMatcher(None, OT, toks(raw), autojunk=False).ratio(), 5), len(raw))
    finally:
        subprocess.run(['rm', '-rf', d])
os.makedirs(O + '/tmp', exist_ok=True)
res = []
with cf.ThreadPoolExecutor(J) as ex:
    for r in ex.map(run, ms): res.append(r)
res.sort(key=lambda r: -(r[1] or 0))
json.dump(res, open(O + f'/sweep-{tag}.json', 'w'))
for r in res[:25]: print(r)
