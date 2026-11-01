#!/usr/bin/env python3
"""rr.py <mn.ll> <out.jsonl> [jobs]  (experiment only; instnamer'd module)
Lever (b): for each plain load %v of execute and each later NON-phi use of %v in another block, insert a volatile re-read
of the same pointer right before that use and let the use take it (models read_volatile at the later use instead of a
spill reload). Scored with the private llc (= SDK bytes)."""
import sys, os, re, json, subprocess, tempfile, hashlib
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import mvload, dvec, ordor
def cands():
    L = mvload.G['L']; B = dvec.blocks_of(L); out = []
    for i, l in enumerate(L):
        m = re.match(r'(\s+)(%[\w.\-]+) = load (?!volatile)(.*)$', l)
        if not m: continue
        v = m.group(2); pat = re.compile(re.escape(v) + r'(?![\w.\-])'); n = 0
        for u in range(i + 1, len(L)):
            if not pat.search(L[u]): continue
            if ' = phi ' in L[u] or B[u] == B[i]: continue
            out.append({'ld': i, 'use': u, 'name': f'rr{i}@{u}'}); n += 1
            if n >= 4: break
    return out
def text(c):
    L = list(mvload.G['L']); l = L[c['ld']]; m = re.match(r'(\s+)(%[\w.\-]+) = load (.*)$', l)
    v = m.group(2); nv = v + '.rr'; pat = re.compile(re.escape(v) + r'(?![\w.\-])')
    L[c['use']] = pat.sub(nv, L[c['use']])
    L.insert(c['use'], f'{m.group(1)}{nv} = load volatile {m.group(3)}')
    return mvload.G['pre'] + '\n'.join(L) + mvload.G['post']
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
    mll, out = sys.argv[1], sys.argv[2]; jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    mvload.setup(mll); C = cands(); print(len(C), 'candidates', file=sys.stderr, flush=True)
    with Pool(jobs, initializer=mvload.init, initargs=(mll,)) as pool, open(out, 'w') as f:
        for r in pool.imap_unordered(run, C, chunksize=4):
            f.write(json.dumps(r) + '\n'); f.flush()
