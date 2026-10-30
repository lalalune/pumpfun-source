#!/usr/bin/env python3
"""regionmap.py <fn.bin | unstripped.so> [seg]: where the unmatched mass of admin_cto is, in source terms.

For each `seg`-instruction segment of the ORIGINAL window: the fraction of its tokens matched
exactly (plain) and after the perfect-frame remap (pf), the unmatched pf token count, and the
landmarks inside it: error-site line immediates and the original's call targets (resolved
through the baseline score.json window symbols, which name our matched functions)."""
import argparse, json, re, struct, sys, difflib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle, framebound  # noqa: E402
from win import demangle  # noqa: E402

LINES = set(range(250, 800))
BASE = Path(__file__).resolve().parents[3] / 'baseline/score.json'


def tokens_of(p):
    if p.endswith('.so'):
        return ctoracle.so_tokens(p)[0]
    raw = Path(p).read_bytes(); out = []; i = 0
    if not raw or len(raw) % 8:
        raise ValueError('raw input must contain whole SBF instructions')
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        if i + n > len(raw):
            raise ValueError('truncated SBF instruction')
        out.append(raw[i:i + n]); i += n
    return out


def short(sym):
    d = demangle(sym)
    d = re.sub(r'<[^<>]*>', '<>', d); d = re.sub(r'<[^<>]*>', '<>', d)
    parts = d.split('::')
    return '::'.join(parts[-2:])[:48]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate')
    parser.add_argument('segment_size', nargs='?', type=int, default=128)
    parser.add_argument('--names', type=Path, default=BASE, help='score report used only for landmark labels')
    args = parser.parse_args()
    if args.segment_size <= 0:
        parser.error('segment size must be positive')
    ctok = tokens_of(args.candidate); seg = args.segment_size
    otok, w = ctoracle.orig_tokens()
    syms = {int(k): v.get('symbols', []) for k, v in json.loads(args.names.read_text(encoding='utf-8'))['windows'].items()}
    starts = sorted(syms)
    import bisect
    def callee(addr):
        k = bisect.bisect_right(starts, addr) - 1
        return short(syms[starts[k]][0]) if k >= 0 and syms[starts[k]] else hex(addr)
    # remap frame offsets of the candidate to the original's (perfect frame)
    r0, r1, _ = framebound.bound(ctok)
    oa = [ctoracle.abstract(t) for t in otok]; ca = [ctoracle.abstract(t) for t in ctok]
    import collections
    sm = difflib.SequenceMatcher(None, oa, ca, autojunk=False)
    votes = collections.defaultdict(collections.Counter)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                fo = framebound.frame_off(otok[i1 + k], otok[i1 + k - 1] if i1 + k else None)
                fc = framebound.frame_off(ctok[j1 + k], ctok[j1 + k - 1] if j1 + k else None)
                if fo and fc and fo[0] == fc[0]:
                    votes[-fc[1]][-fo[1]] += 1
    remap = {c: v.most_common(1)[0][0] for c, v in votes.items()}
    new = []
    for j, t in enumerate(ctok):
        fc = framebound.frame_off(t, ctok[j - 1] if j else None)
        new.append(framebound.setoff(t, fc[0], -remap[-fc[1]]) if fc and -fc[1] in remap else t)
    def matched(c):
        m = [0] * len(otok)
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, otok, c, autojunk=False).get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1): m[i1 + k] = 1
        return m
    m0, m1 = matched(ctok), matched(new)
    addr = []; a = 0
    for t in otok: addr.append(a); a += len(t)
    print(f'ratio {r0}  heuristic-frame-remap {r1}   segments of {seg} original instructions')
    print(f'{"orig off":>8} {"plain":>5} {"pf":>4} {"pf-miss":>7}  landmarks')
    for s in range(0, len(otok), seg):
        e = min(s + seg, len(otok))
        lm = []
        for k in range(s, e):
            t = otok[k]
            if t[0] == 0x85 and (t[1] >> 4) == 1 and t[4:8] != b'\xff\xff\xff\xff':
                imm = struct.unpack_from('<i', w['raw'], addr[k] + 4)[0]
                lm.append(callee(w['start'] + addr[k] + (imm + 1) * 8))
            elif t[0] in (0x62, 0xb7, 0xb4) and struct.unpack_from('<i', t, 4)[0] in LINES:
                lm.append('L%d' % struct.unpack_from('<i', t, 4)[0])
        lm2 = []
        for x in lm:
            if not lm2 or lm2[-1][0] != x: lm2.append([x, 1])
            else: lm2[-1][1] += 1
        txt = ', '.join(f'{x}x{n}' if n > 1 else x for x, n in lm2)
        print(f'{addr[s]:#8x} {sum(m0[s:e]) * 100 // (e - s):4d}% {sum(m1[s:e]) * 100 // (e - s):3d}% {e - s - sum(m1[s:e]):7d}  {txt[:150]}')


if __name__ == '__main__':
    main()
