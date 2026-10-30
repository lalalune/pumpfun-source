#!/usr/bin/env python3
"""irhc.py LO_LABEL HI_LABEL [--w 12] [--j 4] [--rounds 6]: greedy IR block-order hill-climb (llc oracle, not source).
Start = base edits of sweep2 (bb258:bb37, bb261:bb41). Moves: block B (between LO and HI) to after A (within +-W)."""
import sys, os, json, subprocess, argparse, re, tempfile, hashlib
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmove
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-hillclimb'
ap = argparse.ArgumentParser(); ap.add_argument('lo'); ap.add_argument('hi'); ap.add_argument('--w', type=int, default=12)
ap.add_argument('--j', type=int, default=4); ap.add_argument('--rounds', type=int, default=6); ap.add_argument('--start', default='bb258:bb37;bb261:bb41')
a = ap.parse_args()
T0 = open(O + '/ir/best/sh.ll').read()
def build(moves):
    t = T0
    for b, x in moves: t = bmove.move(t, b, x)
    return t
def score(moves):
    t = build(moves)
    h = hashlib.sha1(repr(moves).encode()).hexdigest()[:12]
    p = f'{O}/irhc/{h}.ll'; open(p, 'w').write(t)
    r = subprocess.run([sys.executable, O + '/tools/orc.py', p, '--name', 'irhc_' + h], capture_output=True, text=True)
    os.unlink(p)
    try: d = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return (moves, None)
    subprocess.run(['rm', '-rf', f'{O}/orc/irhc_{h}'])
    return (moves, d)
def main():
    os.makedirs(O + '/irhc', exist_ok=True)
    cur = [tuple(x.split(':')) for x in a.start.split(';') if x]
    _, cd = score(cur); print('START', cur, cd, flush=True)
    def fit(d): return (d['bytes'] == 18584, d['ratio'])
    for rnd in range(a.rounds):
        pre, parts, post = bmove._split(build(cur)); labs = [bmove.lab(p) for p in parts]
        lo, hi = labs.index(a.lo), labs.index(a.hi)
        cands = []
        for i in range(lo, hi + 1):
            for j in range(max(0, i - a.w), min(len(labs), i + a.w + 1)):
                if j in (i, i - 1) or j == 0 and False: continue
                cands.append(cur + [(labs[i], labs[j])])
        print('round', rnd, len(cands), flush=True)
        with Pool(a.j) as pl: res = pl.map(score, cands)
        res = [(m, d) for m, d in res if d]
        res.sort(key=lambda x: fit(x[1]), reverse=True)
        for m, d in res[:5]: print('  ', m[-1], d, flush=True)
        if not res or fit(res[0][1]) <= fit(cd): print('stop'); break
        cur, cd = res[0]; print('ACCEPT', cur, cd, flush=True)
    print('FINAL', cur, cd)

if __name__ == '__main__':
    main()
