#!/usr/bin/env python3
"""Frame probe for admin_cto::execute: r10 offsets of a candidate vs the original window 0x22a10.

  frame.py <unstripped.so> [--orig] [--sym <regex>]

Prints JSON: first r10 store offset, deepest r10 offset, count of distinct r10 offsets, and how many
of the candidate's r10 offsets (as a multiset) occur in the original's multiset.
"""
import json, re, struct, sys
from collections import Counter
from pathlib import Path

H = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
sys.path.insert(0, str(H))
from win import Cand, ORIG, ORIG_SECS, demangle  # noqa: E402
from score import body  # noqa: E402

W, N = 0x22a10, 27400


def r10_offsets(raw):
    out = []
    i = 0
    while i < len(raw):
        op, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
        n = 16 if op == 0x18 else 8
        dst, src = regs & 0xf, regs >> 4
        cls = op & 7
        if cls in (2, 3) and dst == 10:        # st / stx [r10+off]
            out.append(('st', off))
        elif cls == 1 and src == 10:            # ldx rX,[r10+off]
            out.append(('ld', off))
        i += n
    return out


def probe(raw):
    offs = r10_offsets(raw)
    vals = [o for _, o in offs]
    first = next((o for k, o in offs if k == 'st'), None)
    return {'first_store': hex(first & 0xffff) if first is not None else None, 'first_store_dec': first,
            'deepest': min(vals) if vals else None, 'distinct': len(set(vals)), 'n': len(vals)}, Counter(vals)


def fn_bytes(path, sym=r'admin_cto::execute$'):
    c = Cand(path)
    for s, n, nm in c.funcs:
        if re.search(sym, demangle(nm)):
            return c.fn(s, n)
    raise SystemExit('admin_cto::execute not found')


if __name__ == '__main__':
    orig = body(ORIG, ORIG_SECS, W, N)
    po, co = probe(orig)
    if len(sys.argv) > 2 and sys.argv[2] == '--orig':
        print(json.dumps(po)); sys.exit()
    sym = sys.argv[sys.argv.index('--sym') + 1] if '--sym' in sys.argv else r'admin_cto::execute$'
    pc, cc = probe(fn_bytes(sys.argv[1], sym))
    common = sum((cc & co).values())
    pc['common_with_orig'] = common
    pc['orig_n'] = po['n']
    pc['orig_first_store_dec'] = po['first_store_dec']
    pc['orig_deepest'] = po['deepest']
    print(json.dumps(pc))
