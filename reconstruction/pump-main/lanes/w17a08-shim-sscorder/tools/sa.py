#!/usr/bin/env python3
"""sa.py <ssc-dir> <seed> <secs> <out.json>: simulated annealing over the colour processing order with sscsim (ceiling of
spill-colour ORDER alone on fixed code; experiment only)."""
import sys, os, json, random, math, time
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import sscsim
d, seed, secs, out = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
S = sscsim.Sim(d); random.seed(seed)
cur = list(S.order); K = S.colour(cur); m = S.M(S.relabel(K))[0]; best = (m, list(cur)); cache = {}
t0 = time.time(); it = 0; T0 = 2.0
while time.time() - t0 < secs:
    it += 1; temp = T0 * (1 - (time.time() - t0) / secs) + 0.05
    o = list(cur); i = random.randrange(len(o)); s = o.pop(i)
    j = min(len(o), max(0, i + int(random.gauss(0, 12)))) if random.random() < 0.7 else random.randrange(len(o) + 1)
    o.insert(j, s); k = S.colour(o); key = tuple(k[x] for x in S.fis)
    if key in cache: mm = cache[key]
    else: mm = S.M(S.relabel(k))[0]; cache[key] = mm
    if mm >= m or random.random() < math.exp((mm - m) / temp):
        cur, m = o, mm
        if m > best[0]: best = (m, list(cur))
json.dump({'M': best[0], 'order': best[1], 'iters': it, 'uniq': len(cache)}, open(out, 'w'))
print(best[0], it, len(cache))
