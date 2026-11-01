#!/usr/bin/env python3
"""mvload.py <m.ll> <lo> <hi> <span> <out.jsonl> [jobs]  (experiment only)
For each `load` in execute body lines [lo,hi) (with its feeding GEP when that GEP has no other use), move it to each
later legal position (same function, before its first use, up to <span> lines later, never into a trap block, never
before a phi/label), plain and volatile; score with the private llc (= SDK bytes). Models read_volatile / deferred reads."""
import sys, os, re, json, subprocess, tempfile, hashlib
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import dvec, ordor
G = {}
def setup(mll):
    t = open(mll).read(); pre, body, post = dvec.split_module(t); G.update(pre=pre, L=body.split('\n'), post=post)
def uses(L, name, start):
    pat = re.compile(re.escape(name) + r'(?![\w.\-])')
    for k in range(start, len(L)):
        if pat.search(L[k]): return k
    return None
def cands(lo, hi, span):
    L = G['L']; out = []
    blk = dvec.blocks_of(L)
    for i in range(lo, hi):
        m = re.match(r'\s+(%[\w.\-]+) = load (?!volatile)(\S+), ptr (%[\w.\-]+)', L[i])
        if not m: continue
        v, ptr = m.group(1), m.group(3)
        first = uses(L, v, i + 1)
        if first is None: continue
        gi = None
        if re.match(r'\s+' + re.escape(ptr) + r' = getelementptr', L[i - 1]):
            u2 = uses(L, ptr, i + 1)
            if u2 is None: gi = i - 1
        moved = [gi, i] if gi is not None else [i]
        for j in range(i + 1, min(first, i + span) + 1):
            l = L[j]
            if l.strip() == '' or re.match(r'^("[^"]+"|[\w.\-$]+):', l) or ' = phi ' in l: continue
            if 'llvm.trap' in l or l.strip() == 'unreachable': continue
            # do not move past the definition of the pointer operand's users? pointer must dominate: it is defined before i
            for vol in (0, 1):
                out.append({'mv': moved, 'to': j, 'vol': vol, 'name': f'{i}->{j}{"v" if vol else ""}'})
    return out
def text(c):
    L = list(G['L']); moved = [L[k] for k in c['mv']]
    if c['vol']: moved[-1] = moved[-1].replace('= load ', '= load volatile ', 1)
    j = c['to']; keep = [l for k, l in enumerate(L) if k not in c['mv']]
    # insertion index in keep: before original line j (which shifts left by len(mv) since all moved lines are < j)
    idx = j - len(c['mv'])
    keep[idx:idx] = moved
    return G['pre'] + '\n'.join(keep) + G['post']
def init(mll): setup(mll)
def run(c):
    fd, p = tempfile.mkstemp(suffix='.ll'); os.close(fd); open(p, 'w').write(text(c)); fo = p[:-3] + '.o'
    try:
        r = subprocess.run([T + '/llcp.sh', p, '-filetype=obj', '-o', fo], capture_output=True, text=True)
        if r.returncode: return {**c, 'err': r.stderr[-160:]}
        b = dvec.sscsim.oracle.elf_fn(fo, dvec.sscsim.oracle.KEEP); M, ratio = ordor.M(b)
        return {**c, 'M': M, 'ratio': ratio, 'bytes': len(b), 'sig': hashlib.sha1(b).hexdigest()[:10]}
    finally:
        os.remove(p)
        if os.path.exists(fo): os.remove(fo)
if __name__ == '__main__':
    mll, lo, hi, span, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    jobs = int(sys.argv[6]) if len(sys.argv) > 6 else 6
    setup(mll); C = cands(lo, hi, span); print(len(C), 'candidates', file=sys.stderr, flush=True)
    with Pool(jobs, initializer=init, initargs=(mll,)) as pool, open(out, 'w') as f:
        for r in pool.imap_unordered(run, C, chunksize=4):
            f.write(json.dumps(r) + '\n'); f.flush()
