#!/usr/bin/env python3
"""framebound.py <fn.bin | unstripped.so>: exact ratio if every r10 frame offset were the original's.

Aligns our admin_cto tokens with the original's with frame offsets/jumps abstracted (segab style),
votes ours-offset -> orig-offset over the aligned r10 accesses (ldx/st/stx [r10-off] and
mov rX,r10; add64 rX,-off), remaps every one of our frame offsets that has a mapping, and reports
the exact token ratio before and after. The gap is what a perfect frame is worth on this code."""
import collections, difflib, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle  # noqa: E402


def frame_off(t, prev):
    op = t[0]; dst = t[1] & 15; src = t[1] >> 4; cls = op & 7
    if cls == 1 and src == 10 and op != 0x18:
        return ('m', struct.unpack_from('<h', t, 2)[0])
    if cls in (2, 3) and dst == 10:
        return ('m', struct.unpack_from('<h', t, 2)[0])
    if op == 0x07 and prev is not None and prev[0] == 0xbf and (prev[1] >> 4) == 10 and (prev[1] & 15) == dst:
        imm = struct.unpack_from('<i', t, 4)[0]
        if imm < 0:
            return ('a', imm)
    return None


def setoff(t, kind, v):
    b = bytearray(t)
    if kind == 'm':
        struct.pack_into('<h', b, 2, v)
    else:
        struct.pack_into('<i', b, 4, v)
    return bytes(b)


def bound(ctok):
    otok, w = ctoracle.orig_tokens()
    oa = [ctoracle.abstract(t) for t in otok]; ca = [ctoracle.abstract(t) for t in ctok]
    sm = difflib.SequenceMatcher(None, oa, ca, autojunk=False)
    votes = collections.defaultdict(collections.Counter)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            continue
        for k in range(i2 - i1):
            i, j = i1 + k, j1 + k
            fo = frame_off(otok[i], otok[i - 1] if i else None)
            fc = frame_off(ctok[j], ctok[j - 1] if j else None)
            if fo and fc and fo[0] == fc[0]:
                # normalise both to a positive displacement from r10
                votes[-fc[1]][-fo[1]] += 1
    remap = {c: v.most_common(1)[0][0] for c, v in votes.items()}
    new = []
    for j, t in enumerate(ctok):
        fc = frame_off(t, ctok[j - 1] if j else None)
        if fc and -fc[1] in remap:
            t = setoff(t, fc[0], -remap[-fc[1]])
        new.append(t)
    r0 = difflib.SequenceMatcher(None, otok, ctok, autojunk=False).ratio()
    r1 = difflib.SequenceMatcher(None, otok, new, autojunk=False).ratio()
    return round(r0, 5), round(r1, 5), len(remap)


if __name__ == '__main__':
    p = sys.argv[1]
    if p.endswith('.so'):
        ctok, _ = ctoracle.so_tokens(p)
    else:
        raw = Path(p).read_bytes(); ctok = []; i = 0
        while i < len(raw):
            n = 16 if raw[i] == 0x18 else 8; ctok.append(raw[i:i + n]); i += n
    r0, r1, n = bound(ctok)
    print(f'ratio {r0}  perfect-frame ratio {r1}  (offsets remapped: {n})')
