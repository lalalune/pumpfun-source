#!/usr/bin/env python3
"""irsearch.py <name> <slim.ll> [iters] [seed]: hill-climb semantics-preserving IR mutations of
create_v2::execute (instruction moves inside a block, block order) scored by the llc oracle.
Lane-local research tool: finds IR shapes, never a proposal."""
import sys, os, re, random, subprocess, difflib, json, tempfile
from concurrent.futures import ThreadPoolExecutor
L = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w6r1-execute-ir')
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
sys.path.insert(0, L + '/scripts')
import ir
ORIG = ir.orig()
TOK = re.compile(r'%[-\w.$]+|%"[^"]+"')
MEM = re.compile(r'\b(load|store|call|invoke|fence|atomicrmw|cmpxchg)\b')

def split(t):
    m = re.search(r'^define[^\n]*create_v27execute[^\n]*\{\n', t, re.M)
    s = m.end(); e = t.index('\n}\n', s)
    body = t[s:e].split('\n')
    blocks = []; cur = None
    for l in body:
        if re.match(r'^[-\w.$"]+:', l):
            cur = [l, []]; blocks.append(cur)
        elif cur is None:
            cur = ['', []]; blocks.append(cur); cur[1].append(l)
        else:
            cur[1].append(l)
    return t[:s], blocks, t[e:]

def join(pre, blocks, post):
    out = []
    for lab, ins in blocks:
        if lab: out.append(lab)
        out.extend(ins)
    return pre + '\n'.join(out) + post

def defs(l):
    m = re.match(r'\s*(%[-\w.$]+|%"[^"]+") =', l); return m.group(1) if m else None

def uses(l):
    d = defs(l); u = set(TOK.findall(l.split('=', 1)[1] if d else l)); u.discard(d); return u

def is_phi(l): return ' = phi ' in l
def is_term(l): return re.match(r'\s*(br|ret|switch|unreachable|resume)\b', l) is not None
def is_code(l): s = l.strip(); return s and not s.startswith(';')
def memkind(l):
    if 'llvm.lifetime' in l or 'llvm.experimental.noalias' in l: return 'meta'
    if re.search(r'\bload\b', l) and ' = load ' in l: return 'load'
    if MEM.search(l): return 'write'
    return None

def can_swap(a, b):
    """can instruction a (earlier) and b (later) be exchanged"""
    if not (is_code(a) and is_code(b)): return True
    if is_phi(a) or is_phi(b) or is_term(a) or is_term(b): return False
    da, db = defs(a), defs(b)
    if da and da in uses(b): return False
    if db and db in uses(a): return False
    ka, kb = memkind(a), memkind(b)
    if ka == 'write' and kb in ('write', 'load', 'meta'): return False
    if kb == 'write' and ka in ('write', 'load', 'meta'): return False
    if ka == 'meta' and kb == 'meta': return False
    return True

def mutate(blocks, rng):
    b = [[lab, ins[:]] for lab, ins in blocks]
    kind = rng.random()
    if kind < 0.8:
        bi = rng.randrange(len(b)); ins = b[bi][1]
        idx = [i for i, l in enumerate(ins) if is_code(l) and not is_phi(l) and not is_term(l)]
        if not idx: return None, None
        i = rng.choice(idx); d = rng.choice((-1, 1)); steps = rng.randint(1, 6); j = i; moved = 0
        while moved < steps:
            k = j + d
            if k < 0 or k >= len(ins): break
            a_, c_ = (ins[k], ins[j]) if d < 0 else (ins[j], ins[k])
            if not can_swap(a_, c_): break
            ins[j], ins[k] = ins[k], ins[j]; j = k
            if is_code(ins[j - d] if 0 <= j - d < len(ins) else ''): moved += 1
        if j == i: return None, None
        return b, 'mv %s:%d%+d' % (b[bi][0].split(':')[0] or 'entry', i, j - i)
    else:
        if len(b) < 3: return None, None
        i = rng.randrange(1, len(b)); j = rng.randrange(1, len(b))
        if i == j: return None, None
        blk = b.pop(i); b.insert(j, blk)
        return b, 'blk %s %d->%d' % (blk[0].split(':')[0], i, j)

def score(text, tag):
    fd, p = tempfile.mkstemp(suffix='.ll', dir=L + '/tmp'); os.write(fd, text.encode()); os.close(fd)
    o = p[:-3] + '.o'
    try:
        r = subprocess.run([SDK + '/llc', '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', p, '-filetype=obj', '-o', o], capture_output=True, text=True)
        if r.returncode: return -1, None
        c = ir.fn_of(o)
        return difflib.SequenceMatcher(None, ORIG, c, autojunk=False).ratio(), len(c)
    finally:
        for q in (p, o):
            try: os.unlink(q)
            except FileNotFoundError: pass

if __name__ == '__main__':
    name, src = sys.argv[1], sys.argv[2]
    iters = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    rng = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 1)
    os.makedirs(L + '/tmp', exist_ok=True); d = L + '/irsearch/' + name; os.makedirs(d, exist_ok=True)
    import ren; t = ren.ren(open(src).read()); pre, blocks, post = split(t)
    best, n = score(t, 'base'); print('base', best, n, flush=True)
    log = open(d + '/log.txt', 'a'); hist = []
    W = 3
    with ThreadPoolExecutor(W) as ex:
        it = 0
        while it < iters:
            cands = []
            while len(cands) < W:
                nb, desc = mutate(blocks, rng)
                if nb: cands.append((nb, desc))
            res = list(ex.map(lambda c: score(join(pre, c[0], post), c[1]), cands))
            it += W
            for (nb, desc), (r, n) in zip(cands, res):
                if r > best + 1e-9:
                    best = r; blocks = nb; hist.append(desc)
                    print('%5d %.5f %s %s' % (it, r, n, desc), flush=True); log.write('%d %.5f %s\n' % (it, r, desc)); log.flush()
                    open(d + '/best.ll', 'w').write(join(pre, blocks, post))
                    break
    json.dump({'best': best, 'hist': hist}, open(d + '/result.json', 'w'))
    print('final', best, hist)
