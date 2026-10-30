#!/usr/bin/env python3
"""Block-order-insensitive similarity between an original window and a candidate function.

  blocksim.py <unstripped.so> <orig_start> --sym REGEX

Diagnostic only (score.py decides). win.py's ratio is a difflib alignment of the instruction stream,
which collapses when LLVM lays the same blocks out in another order. Here each function is cut into
basic blocks (leaders: entry, jump targets, after jumps/exit); each block becomes a token tuple with
jump offsets and call immediates masked (score.py normalization plus jump offset masking); we report
  block_jaccard: multiset Jaccard over block tuples (exact block identity),
  insn_jaccard:  multiset Jaccard over masked instructions,
  sorted_ratio:  difflib ratio of the two block lists after sorting each (order-free alignment).
"""
import argparse, difflib, re, struct, sys
from collections import Counter
from pathlib import Path

H = Path(__file__).resolve().parents[3] / 'harness'
sys.path.insert(0, str(H))
from score import sections, normalize, body, original_windows  # noqa: E402
from win import Cand, demangle, ORIG_SECS  # noqa: E402

JMP = {0x05} | {op for op in range(0x15, 0xe0) if op & 0x07 in (5, 6) and op & 0xf0 not in (0x80, 0x90)}


def blocks(raw, addr, secs):
    norm = normalize(raw, addr, secs)
    ins = []
    i = 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        ins.append((i, raw[i:i + n], norm[i:i + n])); i += n
    idx = {off: k for k, (off, _, _) in enumerate(ins)}
    leaders = {0}
    for k, (off, r, _) in enumerate(ins):
        op = r[0]
        cls = op & 0x07
        if cls in (5, 6) and op not in (0x85, 0x95, 0x8d):  # jmp class (incl. jmp32), not call/exit
            o = struct.unpack_from('<h', r, 2)[0]
            t = off + 8 + o * 8
            if t in idx:
                leaders.add(t)
            if k + 1 < len(ins):
                leaders.add(ins[k + 1][0])
        if op == 0x95 and k + 1 < len(ins):
            leaders.add(ins[k + 1][0])
    out, cur = [], []
    for off, r, nm in ins:
        if off in leaders and cur:
            out.append(tuple(cur)); cur = []
        b = bytearray(nm)
        if (b[0] & 0x07) in (5, 6) and b[0] not in (0x85, 0x95, 0x8d):
            b[2:4] = b'\0\0'
        cur.append(bytes(b))
    if cur:
        out.append(tuple(cur))
    return out


def jacc(a, b):
    ca, cb = Counter(a), Counter(b)
    return sum((ca & cb).values()) / max(1, sum((ca | cb).values()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cand', type=Path); ap.add_argument('start'); ap.add_argument('--sym', required=True)
    a = ap.parse_args()
    st = int(a.start, 0)
    w = next(x for x in original_windows() if x['start'] == st)
    c = Cand(a.cand)
    picks = [(s, n, nm) for s, n, nm in c.funcs if re.search(a.sym, demangle(nm))]
    ob = blocks(w['raw'], st, ORIG_SECS)
    for s, n, nm in picks:
        cb = blocks(c.fn(s, n), s, c.secs)
        oi = [x for b in ob for x in b]; ci = [x for b in cb for x in b]
        so, sc = sorted(ob), sorted(cb)
        print({'symbol': demangle(nm), 'cand_bytes': n, 'orig_bytes': w['bytes'], 'blocks': (len(ob), len(cb)),
               'block_jaccard': round(jacc(ob, cb), 4), 'insn_jaccard': round(jacc(oi, ci), 4),
               'sorted_ratio': round(difflib.SequenceMatcher(None, [x for b in so for x in b], [x for b in sc for x in b], autojunk=False).ratio(), 4)})


if __name__ == '__main__':
    main()
