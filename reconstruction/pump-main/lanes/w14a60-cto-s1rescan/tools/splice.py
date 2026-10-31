#!/usr/bin/env python3
"""splice.py: whole-window residual map for admin_cto::execute (0x22a10).

  splice.py load <unstripped.so>              -> prints ratio/slots (sanity vs target_metric)
  splice.py chunks <so> [--step 0x400]        -> per-chunk local residual split (fm/rm/jm/sk)
  splice.py anchors <so> [--min 4]            -> equal-offset anchor runs (L3 skeleton equal)
  splice.py regions <so> [--min 4]            -> splice orig bytes over each gap between anchors;
                                                 dratio/dslots per region + fm/rm/jm/sk split
  splice.py range <so> lo hi [lo hi ...]      -> splice what-if for given byte ranges (window offsets)

Levels: L0 = score.normalize tokens (what ratio uses). L1 = L0 with r10-frame displacements and
negative add64 immediates masked (fm). L2 = L1 with registers masked (rm). L3 = L2 with jump
offsets masked (jm). sk = L3 misses (opcode/immediate/structure).
"""
import sys, struct, difflib, json
from pathlib import Path
H = Path(__file__).resolve().parents[4] / 'harness'
sys.path.insert(0, str(H))
from score import original_windows, normalize  # noqa
from win import Cand, ORIG_SECS  # noqa
import re
W = 0x22a10
SYM = re.compile(r'admin_cto.*execute')

def toks(raw, addr, secs):
    norm = normalize(raw, addr, secs)
    out = []; i = 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        out.append((i, bytes(norm[i:i+n]))); i += n
    return out

def mask(t, lvl):
    if lvl == 0: return t
    b = bytearray(t); op = b[0]; dst = b[1] & 15; src = b[1] >> 4
    cls = op & 7
    if cls in (1, 2, 3) and (dst == 10 or src == 10):  # ldx/st/stx with frame
        b[2:4] = b'\0\0'
    if op == 0x07 and struct.unpack_from('<i', b, 4)[0] < 0:
        b[4:8] = b'\0\0\0\0'
    if lvl >= 2: b[1] = 0
    if lvl >= 3 and cls in (5, 6) and op not in (0x85, 0x95, 0x8d):
        b[2:4] = b'\0\0'
    return bytes(b)

def load(so):
    w = {x['start']: x for x in original_windows()}[W]
    c = Cand(so)
    picks = [(s, n) for s, n, nm in c.funcs if SYM.search(nm)]
    from win import demangle
    picks = [(s, n) for s, n, nm in c.funcs if SYM.search(demangle(nm))] or picks
    s, n = picks[0]
    craw = c.fn(s, n)
    o = toks(w['raw'], W, ORIG_SECS); k = toks(craw, s, c.secs)
    return o, k, w['norm'], normalize(craw, s, c.secs)

def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

def slots(on, cn):
    if len(on) != len(cn): return None
    return sum(1 for i in range(0, len(on), 8) if on[i:i+8] != cn[i:i+8])

def idx(tl):
    return {off: j for j, (off, _) in enumerate(tl)}

def local(o, k, lo, hi, lvl):
    a = [mask(t, lvl) for off, t in o if lo <= off < hi]
    b = [mask(t, lvl) for off, t in k if lo <= off < hi]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    m = sum(x.size for x in sm.get_matching_blocks())
    return len(a), len(b), len(a) - m

def split(o, k, lo, hi):
    r = {}
    miss = [local(o, k, lo, hi, l)[2] for l in range(4)]
    for l in range(1, 4): miss[l] = min(miss[l], miss[l-1])
    na, nb, _ = local(o, k, lo, hi, 0)
    return dict(n_orig=na, n_cand=nb, miss=miss[0], fm=miss[0]-miss[1], rm=miss[1]-miss[2], jm=miss[2]-miss[3], sk=miss[3])

def splice(o, k, on, cn, ranges):
    oi, ki = idx(o), idx(k)
    keep = []
    cn2 = bytearray(cn)
    for lo, hi in ranges:
        assert lo in oi and lo in ki and (hi in oi or hi == len(on)) and (hi in ki or hi == len(cn)), (hex(lo), hex(hi))
        cn2[lo:hi] = on[lo:hi]
    newk = [t for t in k if not any(lo <= t[0] < hi for lo, hi in ranges)] + [t for t in o if any(lo <= t[0] < hi for lo, hi in ranges)]
    newk.sort()
    return [t for _, t in newk], bytes(cn2)

def anchors(o, k, minrun=4, lvl=3):
    """Equal-offset runs where L<lvl> tokens are equal, of >= minrun instructions."""
    oi = dict(o); ki = dict(k)
    runs = []; cur = None
    for off, t in o:
        eq = off in ki and mask(ki[off], lvl) == mask(t, lvl)
        if eq:
            if cur is None: cur = [off, off, 0]
            cur[1] = off + len(t); cur[2] += 1
        else:
            if cur and cur[2] >= minrun: runs.append(tuple(cur))
            cur = None
    if cur and cur[2] >= minrun: runs.append(tuple(cur))
    return runs

def main():
    cmd, so = sys.argv[1], sys.argv[2]
    o, k, on, cn = load(so)
    base_r = ratio([t for _, t in o], [t for _, t in k]); base_s = slots(on, cn)
    args = sys.argv[3:]
    opt = lambda name, d: int(args[args.index(name)+1], 0) if name in args else d
    if cmd == 'load':
        print(json.dumps(dict(ratio=round(base_r, 5), slots=base_s, n_orig=len(o), n_cand=len(k)))); return
    if cmd == 'chunks':
        st = opt('--step', 0x400)
        for lo in range(0, len(on), st):
            print(hex(lo), json.dumps(split(o, k, lo, lo+st)))
        return
    if cmd == 'anchors':
        for r in anchors(o, k, opt('--min', 4), opt('--lvl', 3)):
            print(hex(r[0]), hex(r[1]), r[2])
        return
    if cmd in ('regions', 'range', 'fixed'):
        if cmd == 'regions':
            an = anchors(o, k, opt('--min', 4), opt('--lvl', 3))
            gaps = []; prev = 0
            for a0, a1, _ in an:
                if a0 > prev: gaps.append((prev, a0))
                prev = a1
            if prev < len(on): gaps.append((prev, len(on)))
            minsz = opt('--minsz', 0)
            gaps = [g for g in gaps if g[1]-g[0] >= minsz]
        elif '--step' in args:
            st = opt('--step', 0x200); oi, ki = idx(o), idx(k)
            pts = [0]
            for x in range(st, len(on), st):
                while not (x in oi and x in ki): x += 8
                pts.append(x)
            pts.append(len(on)); gaps = list(zip(pts, pts[1:]))
        else:
            v = [int(x, 0) for x in args if not x.startswith('--')]
            gaps = list(zip(v[::2], v[1::2]))
        print(json.dumps(dict(base_ratio=round(base_r, 5), base_slots=base_s)))
        rows = []
        for lo, hi in gaps:
            nk, ncn = splice(o, k, on, cn, [(lo, hi)])
            r = ratio([t for _, t in o], nk); s = slots(on, ncn)
            row = dict(lo=hex(lo), hi=hex(hi), dratio=round(r-base_r, 5), dslots=base_s - s, **split(o, k, lo, hi))
            rows.append(row); print(json.dumps(row), flush=True)
        return

if __name__ == '__main__':
    main()
