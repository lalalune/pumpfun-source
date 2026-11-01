#!/usr/bin/env python3
"""rrpair.py <mn.ll> <rr.jsonl> <anchor ld@use> <base M> [jobs]: the anchor rr cell combined with every other rr cell (experiment only)."""
import sys, os, re, json, subprocess, tempfile
from multiprocessing import Pool
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import mvload, dvec, ordor
def text2(cs):
    L = list(mvload.G['L'])
    for c in sorted(cs, key=lambda c: -c['use']):
        l = L[c['ld']]; m = re.match(r'(\s+)(%[\w.\-]+) = load (.*)$', l)
        v = m.group(2); nv = v + '.rr%d' % c['use']; pat = re.compile(re.escape(v) + r'(?![\w.\-])')
        L[c['use']] = pat.sub(nv, L[c['use']]); L.insert(c['use'], f'{m.group(1)}{nv} = load volatile {m.group(3)}')
    return mvload.G['pre'] + '\n'.join(L) + mvload.G['post']
def run(cs):
    fd, p = tempfile.mkstemp(suffix='.ll'); os.close(fd); open(p, 'w').write(text2(cs)); fo = p[:-3] + '.o'
    r = subprocess.run([T + '/llcp.sh', p, '-filetype=obj', '-o', fo], capture_output=True, text=True); os.remove(p)
    if r.returncode: return {'e': cs, 'err': r.stderr[-100:]}
    b = dvec.sscsim.oracle.elf_fn(fo, dvec.sscsim.oracle.KEEP); os.remove(fo)
    return {'e': [f"rr{c['ld']}@{c['use']}" for c in cs], 'M': ordor.M(b)[0], 'bytes': len(b)}
if __name__ == '__main__':
    mll, rf, anc = sys.argv[1], sys.argv[2], sys.argv[3]; jobs = int(sys.argv[5]) if len(sys.argv) > 5 else 4
    mvload.setup(mll); a = dict(zip(('ld', 'use'), map(int, anc[2:].split('@'))))
    R = [json.loads(l) for l in open(rf)]
    C = [[a, {'ld': r['ld'], 'use': r['use']}] for r in R if 'err' not in r and not (r['ld'] == a['ld'] and r['use'] == a['use'])]
    with Pool(jobs, initializer=mvload.init, initargs=(mll,)) as pool:
        out = list(pool.imap_unordered(run, C, chunksize=4))
    out = [o for o in out if 'err' not in o]
    out.sort(key=lambda o: -(o['M'] + (0 if o['bytes'] == 27400 else -1000)))
    for o in out[:12]: print(o)
