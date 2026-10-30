#!/usr/bin/env python3
"""Frame map: align original vs candidate admin_cto with r10 offsets masked, then list
(orig offset -> cand offset) pairs for r10-relative accesses in matched instructions.
  framemap.py <unstripped.so> [--sym REGEX]"""
import sys, struct, difflib, re
from collections import Counter, defaultdict
sys.path.insert(0, '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
from score import normalize, original_windows
from win import Cand, demangle

def toks(raw):
    out = []; i = 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        op = raw[i]; regs = raw[i+1]; dst = regs & 15; src = regs >> 4
        off = struct.unpack_from('<h', raw, i+2)[0]
        imm = struct.unpack_from('<i', raw, i+4)[0]
        r10 = None
        cls = op & 7
        # ldx (cls 1) uses src as base; st/stx (cls 2/3) use dst as base
        if cls == 1 and src == 10: r10 = off
        if cls in (2, 3) and dst == 10: r10 = off
        # mov64 rX, r10 ; add64 rX, imm  -> lea pattern, mask the add imm separately
        key = (op, dst, src, None if r10 is not None else off, imm, raw[i+8:i+16] if n == 16 else b'')
        out.append((key, r10, i)); i += n
    return out

def summary(so, sym=r'admin_cto::execute$'):
    w = {w['start']: w for w in original_windows()}[0x22a10]
    c = Cand(so)
    pat = re.compile(sym)
    s, n, nm = [(s, n, nm) for s, n, nm in c.funcs if pat.search(demangle(nm)) or pat.search(nm)][0]
    craw = normalize(c.fn(s, n), s, c.secs)
    O = _fold(toks(w['norm'])); C = _fold(toks(craw))
    sm = difflib.SequenceMatcher(None, [x[0] for x in O], [x[0] for x in C], autojunk=False)
    pairs = []
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            if O[a+k][1] is not None:
                pairs.append((O[a+k][1], C[b+k][1]))
    eq = sum(1 for p in pairs if p[0] == p[1])
    m = defaultdict(Counter)
    for o, cc in pairs: m[o][cc] += 1
    firstdiv = None
    for o in sorted(m, reverse=True):
        top = m[o].most_common(1)[0]
        if top[0] != o and sum(m[o].values()) >= 2:
            firstdiv = -o; break
    return {'masked_ratio': round(sm.ratio(), 5), 'r10_pairs': len(pairs), 'r10_equal': eq, 'first_div_T': firstdiv}


def _fold(t):
    out = []
    for k, (key, r10, i) in enumerate(t):
        if key[0] == 0x07 and k > 0 and t[k-1][0][0] == 0xbf and t[k-1][0][2] == 10 and t[k-1][0][1] == key[1]:
            out.append(((0x07, key[1], 0, 0, None, b''), key[4], i))
        else:
            out.append((key, r10, i))
    return out


def main():
    so = sys.argv[1]; sym = sys.argv[3] if len(sys.argv) > 3 else r'admin_cto::execute$'
    w = {w['start']: w for w in original_windows()}[0x22a10]
    c = Cand(so)
    pat = re.compile(sym)
    s, n, nm = [(s, n, nm) for s, n, nm in c.funcs if pat.search(demangle(nm)) or pat.search(nm)][0]
    craw = normalize(c.fn(s, n), s, c.secs)
    oraw = w['norm']
    # fold lea: add64 rX, imm after mov64 rX, r10 -> treat imm as r10 offset
    def fold(t):
        out = []
        for k, (key, r10, i) in enumerate(t):
            if key[0] == 0x07 and k > 0 and t[k-1][0][0] == 0xbf and t[k-1][0][2] == 10 and t[k-1][0][1] == key[1]:
                out.append(((0x07, key[1], 0, 0, None, b''), key[4], i))
            else:
                out.append((key, r10, i))
        return out
    O = fold(toks(oraw)); C = fold(toks(craw))
    sm = difflib.SequenceMatcher(None, [x[0] for x in O], [x[0] for x in C], autojunk=False)
    pairs = []
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            if O[a+k][1] is not None:
                pairs.append((O[a+k][1], C[b+k][1]))
    eq = sum(1 for p in pairs if p[0] == p[1])
    print(f'masked ratio {sm.ratio():.4f}; r10 pairs {len(pairs)}, equal {eq}')
    m = defaultdict(Counter)
    for o, cc in pairs: m[o][cc] += 1
    print('orig_off  -> cand_off(count) ... delta')
    for o in sorted(m, reverse=True):
        top = m[o].most_common(3)
        print(f'{o:6d} {hex(-o) if o<0 else o:>7} -> ' + ' '.join(f'{cc}({k})' for cc, k in top) + f'   d={o-top[0][0]}')
if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == '--summary':
        import json; print(json.dumps(summary(sys.argv[1])))
    else:
        main()
