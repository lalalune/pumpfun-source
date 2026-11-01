#!/usr/bin/env python3
"""votes.py <ssc-dir>: per spill interval, the original's spill offsets at skeleton-aligned accesses (experiment only).
Alignment: difflib on scorer-masked tokens with every r10 spill offset blanked (ours: no-share build; orig: <= -2264)."""
import sys, os, json, difflib, collections
T = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, T)
import sscsim
def toks(raw, spill):
    out = []; meta = []; i = 0
    while i < len(raw):
        op = raw[i]; n = 16 if op == 0x18 else 8; t = bytearray(raw[i:i+n])
        if op == 0x85: t[1] &= 0x0f; t[4:8] = b'\0'*4
        if op == 0x18: t[4:8] = b'\0'*4; t[12:16] = b'\0'*4
        off = None
        if op in (0x79, 0x7b):
            base = (raw[i+1] >> 4) if op == 0x79 else (raw[i+1] & 15)
            o = int.from_bytes(raw[i+2:i+4], 'little', signed=True)
            if base == 10 and spill(o): off = o; t[2:4] = b'\0\0'
        out.append(bytes(t)); meta.append(off); i += n
    return out, meta
def run(d):
    S = sscsim.Sim(d); orig = sscsim.oracle.orig_window()
    a, am = toks(orig, lambda o: o <= -2264 and o % 8 == 0)
    b, bm = toks(S.ns, lambda o: o in S.ns_off)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    V = collections.defaultdict(collections.Counter); n = 0
    for blk in sm.get_matching_blocks():
        for x in range(blk.size):
            oo, bo = am[blk.a + x], bm[blk.b + x]
            if oo is not None and bo is not None:
                V[S.ns_off[bo]][(-2264 - oo) // 8] += 1; n += 1
    return S, V, n
if __name__ == '__main__':
    S, V, n = run(sys.argv[1]); k = S.colour(S.order)
    print('aligned spill pairs', n)
    good = sum(V[s][k[s]] for s in V); tot = sum(sum(V[s].values()) for s in V)
    print('votes on current colour', good, 'of', tot)
    rows = []
    for r, s in enumerate(S.order):
        v = V.get(s, {}); top = v.most_common(3) if v else []
        rows.append((r, s, round(S.W[s], 7), k[s], top))
        print(f'{r:3d} SS#{s} w={S.W[s]:.6e} k{k[s]:<3d} orig: ' + ' '.join(f'k{c}x{m}' for c, m in top))
    json.dump({str(s): dict(V[s]) for s in V}, open(sys.argv[1] + '/votes.json', 'w'))
