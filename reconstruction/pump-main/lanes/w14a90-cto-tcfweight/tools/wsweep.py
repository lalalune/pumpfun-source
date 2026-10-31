#!/usr/bin/env python3
"""wsweep.py base.ll out.jsonl [vals...]: spill-weight probes on the TCF CpiContext final-store block (post-opt IR, llc only).
For each piece value V stored into %_55.i102 in the final block: early (store at def), head/tail of final block, dup (extra
store in the block after def). Experiment only."""
import sys, os, re, json, subprocess
D = os.path.dirname(os.path.abspath(__file__))
src = open(D + '/rx.py').read(); g = {'__name__': 'x'}; exec(src[:src.index("OUT=os.environ.get")], g)
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
OUT = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a90-cto-tcfweight')
base, outf = sys.argv[1], sys.argv[2]; T = open(base).read()
L = T.split('\n')
CTX = '%_55.i102'
call = next(i for i, l in enumerate(L) if 'transfer_creator_fees_to_pump_v2' in l and 'call' in l)
fb = call
while not re.match(r'^\S.*:', L[fb]): fb -= 1   # final block label
geps = {}
for i in range(fb, call):
    m = re.match(r'\s+(%\S+) = getelementptr inbounds i8, ptr ' + re.escape(CTX) + r', i64 (\d+)$', L[i])
    if m: geps[m.group(1)] = int(m.group(2))
stores = {}
for i in range(fb, call):
    m = re.match(r'\s+store (ptr|i64|i8) (%\S+), ptr (%\S+), align (\d+)', L[i])
    if m and (m.group(3) in geps or m.group(3) == CTX):
        stores[m.group(2)] = (i, m.group(1), geps.get(m.group(3), 0), m.group(4))
def defline(v):
    pat = '  ' + v + ' = '
    return next(i for i, l in enumerate(L) if l.startswith(pat))
def blockend(i):
    j = i
    while not L[j].lstrip().startswith('br '): j += 1
    return j
def nextblock_first(i):
    j = blockend(i) + 1
    while not re.match(r'^\S.*:', L[j]): j += 1
    # if block is trap block, skip it
    while 'llvm.trap' in L[j + 1]:
        j += 1
        while not re.match(r'^\S.*:', L[j]): j += 1
    return j + 1
def mk(v, mode):
    i, ty, off, al = stores[v]
    st = lambda nm: [f'  %w_{nm} = getelementptr inbounds i8, ptr {CTX}, i64 {off}', f'  store {ty} {v}, ptr %w_{nm}, align {al}, !noalias !8628']
    M = L[:]
    if mode == 'early':
        d = defline(v); M[i] = ''; M[d + 1:d + 1] = st('e')
    elif mode == 'head':
        M[i] = ''; M[fb + 1:fb + 1] = st('h')
    elif mode == 'tail':
        M[i] = ''; M[call:call] = st('t')
    elif mode == 'dup':
        d = defline(v); n = nextblock_first(d)
        if n >= fb: return None
        M[n:n] = st('d')
    elif mode == 'dupfb':
        M[fb + 1:fb + 1] = st('df')
    return '\n'.join(M)
def run(name, t):
    d = OUT + '/sw/' + name; os.makedirs(d, exist_ok=True); open(d + '/m.ll', 'w').write(t)
    r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', d + '/m.ll', '-filetype=obj', '-o', d + '/m.o'], capture_output=True, text=True)
    if r.returncode: return {'name': name, 'err': r.stderr[-300:]}
    cand = g['elf_fn'](d + '/m.o', g['KEEP']); open(d + '/fn.bin', 'wb').write(cand)
    rr, sd = g['metric'](cand, g['orig_window']())
    f = subprocess.run([sys.executable, D + '/fmr.py', d + '/fn.bin'], capture_output=True, text=True).stdout.split()
    os.remove(d + '/m.o'); os.remove(d + '/m.ll')
    lv = [float(x.strip('[],')) for x in f[2:5]]; ch = [int(x) for x in f[5:]]
    return {'name': name, 'ratio': round(rr, 5), 'bytes': len(cand), 'slots': sd, 'L': lv, 'ch': ch}
vals = sys.argv[3:] or list(stores)
modes = os.environ.get('MODES', 'early head tail dup dupfb').split()
with open(outf, 'a') as fo:
    for v in vals:
        if v not in stores: print('missing', v); continue
        for mode in modes:
            t = mk(v, mode)
            if t is None: continue
            r = run(v.strip('%').replace('.', '_') + '-' + mode, t); r['v'] = v; r['mode'] = mode
            fo.write(json.dumps(r) + '\n'); fo.flush(); print(json.dumps(r))
