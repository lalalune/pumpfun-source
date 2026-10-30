#!/usr/bin/env python3
"""irclimb.py IN.ll --name N [--rounds K] [--jobs J] [--families f1,f2]: greedy hill-climb of swap_hop post-opt IR
under the llc oracle. Mutation families: pol (flip icmp eq/ne polarity + swap br targets), brswap (negate a br
condition with xor and swap targets), blk (move a block to just before/after another block within +-W
positions), insup/insdn (move one non-phi, non-terminator instruction up/down by one inside its block).
Objective: original size first, then masked ratio. Writes OUT/climb/N/{best.ll,log.jsonl}."""
import sys, os, re, subprocess, difflib, argparse, json, random, tempfile
from concurrent.futures import ThreadPoolExecutor
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-ir')
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ap = argparse.ArgumentParser(); ap.add_argument('ll'); ap.add_argument('--name', required=True)
ap.add_argument('--rounds', type=int, default=3); ap.add_argument('--jobs', type=int, default=6)
ap.add_argument('--families', default='pol,brswap,blk,insup,insdn'); ap.add_argument('--win', type=int, default=3)
ap.add_argument('--region', default='', help='only blocks whose label matches this regex')
ap.add_argument('--limit', type=int, default=0)
a = ap.parse_args()
D = f'{O}/climb/{a.name}'; os.makedirs(D, exist_ok=True)
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
def score(text, tag):
    with tempfile.TemporaryDirectory(dir=D) as td:
        open(td + '/m.ll', 'w').write(text)
        r = subprocess.run([L + '/llc', '-O3', '-mtriple=sbf', '-mattr=+store-imm,+jmp-ext', '-relocation-model=pic', '-function-sections',
                            '-data-sections', '-filetype=obj', td + '/m.ll', '-o', td + '/m.o'], capture_output=True, text=True)
        if r.returncode: return None
        secs = subprocess.run([L + '/llvm-objdump', '-h', td + '/m.o'], capture_output=True, text=True).stdout
        sec = next(l.split()[1] for l in secs.splitlines() if 'multi_hop_curve8swap_hop17h' in l and '.rel' not in l)
        subprocess.run([L + '/llvm-objcopy', '-O', 'binary', '--only-section=' + sec, td + '/m.o', td + '/m.bin'], check=True)
        raw = open(td + '/m.bin', 'rb').read()
    c = toks(raw)
    return (len(raw) == len(oraw), round(difflib.SequenceMatcher(None, OT, c, autojunk=False).ratio(), 5), len(raw))
def fnsplit(t):
    m = re.search(r'^define [^\n]*multi_hop_curve8swap_hop17h[^\n]*\{\n', t, re.M)
    s = m.end(); e = t.index('\n}\n', s)
    return t[:s], t[s:e], t[e:]
def denum(body):
    body = re.sub(r'%(\d+)\b', r'%v\1', body)
    return re.sub(r'^(\d+):', r'v\1:', body, flags=re.M)
def blocks(body):
    out = []; cur = None
    for l in body.split('\n'):
        m = re.match(r'^("[^"]+"|[\w.$-]+):', l)
        if m: cur = [m.group(1), [l]]; out.append(cur)
        elif cur is None: cur = ['__entry', [l]]; out.append(cur)
        else: cur[1].append(l)
    return out
def join(bl): return '\n'.join('\n'.join(ls) for _, ls in bl)
def is_ins(l): return l.startswith('  ') and not l.startswith('  br ') and not l.startswith('  switch ') and not l.startswith('  ret ') and not l.startswith('  unreachable') and ' = phi ' not in l
def mutations(bl, fams, rx):
    out = []
    lab = [b[0] for b in bl]
    sel = [i for i, b in enumerate(bl) if (not rx or re.search(rx, b[0]))]
    for i in sel:
        name, ls = bl[i]
        for j, l in enumerate(ls):
            if 'pol' in fams:
                m = re.match(r'  (%\S+) = icmp (eq|ne) (i\d+) (%\S+), (\S+)$', l)
                if m:
                    v = m.group(1)
                    for k in range(j + 1, len(ls)):
                        mb = re.match(r'  br i1 ' + re.escape(v) + r', label (%\S+), label (%\S+)$', ls[k])
                        if mb:
                            out.append(('pol', name, j, k, m.groups(), mb.groups())); break
            if 'brswap' in fams:
                mb = re.match(r'  br i1 (%\S+), label (%\S+), label (%\S+)$', l)
                if mb: out.append(('brswap', name, j))
        if 'insup' in fams or 'insdn' in fams:
            for j, l in enumerate(ls):
                if j == 0 or not is_ins(l) or l.startswith('  call void @llvm.dbg'): continue
                if 'insup' in fams and j > 1 and is_ins(ls[j - 1]): out.append(('insup', name, j))
                if 'insdn' in fams and j + 1 < len(ls) and is_ins(ls[j + 1]): out.append(('insdn', name, j))
        if 'blk' in fams and i > 0:
            for d in range(-a.win, a.win + 1):
                if d in (0, 1) or not (1 <= i + d <= len(bl)): continue
                out.append(('blk', name, d))
    return out
def apply(bl, mu):
    bl = [[n, list(ls)] for n, ls in bl]
    idx = {b[0]: k for k, b in enumerate(bl)}
    kind, name = mu[0], mu[1]; i = idx[name]; ls = bl[i][1]
    if kind == 'pol':
        _, _, j, k, (v, op, ty, x, y), (A, B) = mu
        ls[j] = f'  {v} = icmp {"ne" if op == "eq" else "eq"} {ty} {x}, {y}'
        ls[k] = f'  br i1 {v}, label {B}, label {A}'
    elif kind == 'brswap':
        j = mu[2]; mb = re.match(r'  br i1 (%\S+), label (%\S+), label (%\S+)$', ls[j])
        c = mb.group(1); n = c + '.inv' + str(j)
        ls[j:j + 1] = [f'  {n} = xor i1 {c}, true', f'  br i1 {n}, label {mb.group(3)}, label {mb.group(2)}']
    elif kind in ('insup', 'insdn'):
        j = mu[2]; k = j - 1 if kind == 'insup' else j + 1
        ls[j], ls[k] = ls[k], ls[j]
    elif kind == 'blk':
        d = mu[2]; b = bl.pop(i); bl.insert(i + d if d < 0 else i + d - 1, b)
    return bl
t0 = open(a.ll).read()
pre, body, post = fnsplit(t0)
bl = blocks(denum(body))
best = score(pre + join(bl) + post, 'base'); print(json.dumps({'base': best}), flush=True)
log = open(D + '/log.jsonl', 'a')
fams = a.families.split(',')
for rnd in range(a.rounds):
    mus = mutations(bl, fams, a.region)
    if a.limit: random.seed(rnd); mus = random.sample(mus, min(a.limit, len(mus)))
    print(json.dumps({'round': rnd, 'mutations': len(mus)}), flush=True)
    def ev(mu):
        try: nb = apply(bl, mu)
        except Exception as e: return mu, None, None
        return mu, nb, score(pre + join(nb) + post, str(mu[:3]))
    results = []
    with ThreadPoolExecutor(a.jobs) as ex:
        for mu, nb, s in ex.map(ev, mus):
            if s is None: continue
            results.append((s, mu, nb))
            if s[:2] > best[:2]:
                log.write(json.dumps({'round': rnd, 'mu': [str(x) for x in mu[:3]], 'score': s}) + '\n'); log.flush()
    results.sort(key=lambda r: r[0][:2], reverse=True)
    if not results or results[0][0][:2] <= best[:2]: print('no improvement'); break
    best, mu, bl = results[0]
    print(json.dumps({'round': rnd, 'accept': [str(x) for x in mu[:3]], 'score': best}), flush=True)
    open(D + '/best.ll', 'w').write(pre + join(bl) + post)
    for s, m2, _ in results[1:8]: print('   alt', s, [str(x) for x in m2[:3]])
