#!/usr/bin/env python3
"""tab.py <name>=<fn.bin|.so> ... [--masks none,r,f,rf,rfj] [--json out.jsonl]
Union-table helper (experiment only): for each candidate, the true-LCS matched original tokens per w17a01 region
(rc.py's map and token masks) at each mask level, plus the scorer's difflib M and the byte size.
Runs one process per (candidate, mask)."""
import sys, os, json, difflib, multiprocessing as mp
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import rc

_O = None
def O():
    global _O
    if _O is None:
        _O = rc.mask(rc.orig_window())
    return _O

def job(arg):
    name, path, m = arg
    ot, oo = O()
    d, t, ra, M, b = rc.per(path, ot, oo, m)
    return name, m or 'none', d, t, ra, M, b

if __name__ == '__main__':
    a = sys.argv[1:]; masks = ['none', 'r', 'f', 'rf', 'rfj']; jo = None
    if '--masks' in a:
        i = a.index('--masks'); masks = a[i + 1].split(','); del a[i:i + 2]
    if '--json' in a:
        i = a.index('--json'); jo = a[i + 1]; del a[i:i + 2]
    C = [x.split('=', 1) for x in a]
    jobs = [(n, p, m.replace('none', '')) for n, p in C for m in masks]
    with mp.Pool(min(6, len(jobs))) as pool:
        res = pool.map(job, jobs)
    ot, oo = O(); tot = {}
    for o in oo:
        r = rc.reg_of(o); tot[r] = tot.get(r, 0) + 1
    R = {}
    for name, m, d, t, ra, M, b in res:
        R.setdefault(name, {'name': name, 'M': M, 'ratio': ra, 'bytes': b, 'lcs': {}, 'reg': {}})
        R[name]['lcs'][m] = t; R[name]['reg'][m] = d
    names = [n for n, _ in C]
    print('%-12s %6s %6s ' % ('cand', 'M', 'bytes') + ' '.join('%6s' % m for m in masks))
    for n in names:
        x = R[n]
        print('%-12s %6d %6d ' % (n, x['M'], x['bytes']) + ' '.join('%6d' % x['lcs'][m] for m in masks))
    ref = names[0]
    for m in masks:
        print('-- mask %s: per-region delta vs %s (orig tokens: %s)' % (m, ref, ' '.join('%s:%d' % (r, tot[r]) for _, r in rc.REG)))
        for n in names[1:]:
            d0 = R[ref]['reg'][m]; d = R[n]['reg'][m]
            print('   %-12s %+5d  ' % (n, R[n]['lcs'][m] - R[ref]['lcs'][m]) + ' '.join('%s:%+d' % (r, d.get(r, 0) - d0.get(r, 0)) for _, r in rc.REG if d.get(r, 0) != d0.get(r, 0)))
    if jo:
        with open(jo, 'a') as f:
            for n in names:
                f.write(json.dumps(R[n]) + '\n')
