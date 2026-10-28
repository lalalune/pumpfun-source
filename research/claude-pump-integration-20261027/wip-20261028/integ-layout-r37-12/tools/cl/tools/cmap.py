"""Counterpart map: original window -> candidate function, via matched parents and aligned call sites."""
import sys, difflib
sys.path.insert(0, '.')
from an import *


def ops(raw):
    """token per instruction: (opcode, regs) except calls -> 'CALL' (target masked)."""
    t = []
    for off, n in insn_offsets(raw):
        op = raw[off]
        if op == 0x85:
            t.append(('call', raw[off + 1] >> 4))
        elif op == 0x18:
            t.append((op, raw[off + 1]))
        else:
            t.append((op, raw[off + 1], raw[off + 2:off + 4]))
    return t


def aligned_calls(Ow, Cf):
    """pairs (orig_target, cand_target) of internal calls aligned by an instruction-level diff."""
    oi = insn_offsets(Ow['raw']); ci = insn_offsets(Cf['raw'])
    ot = ops(Ow['raw']); ct = ops(Cf['raw'])
    ocall = {off: t for off, t in Ow['calls']}; ccall = {off: t for off, t in Cf['calls']}
    sm = difflib.SequenceMatcher(None, ot, ct, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('equal',) or (tag == 'replace' and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                oo = oi[i1 + k][0]; co = ci[j1 + k][0]
                if oo in ocall and co in ccall:
                    out.append((ocall[oo], ccall[co], tag))
    return out, sm.ratio()


def build(O, C, M, seeds=None, max_rounds=6, min_ratio=0.5):
    """cp[orig] = (cand, how). Seeds: matched windows with a unique candidate."""
    cp = {}
    for st, ms in M.items():
        if len(ms) == 1:
            cp[st] = (ms[0], 'match')
    if seeds:
        for st, a in seeds.items():
            cp.setdefault(st, (a, 'seed'))
    frontier = list(cp)
    seen = set()
    rnd = 0
    while frontier and rnd < max_rounds:
        rnd += 1
        nxt = []
        for st in frontier:
            if st in seen:
                continue
            seen.add(st)
            a, how = cp[st]
            Ow = O[st]; Cf = C[a]
            if how == 'match':
                oc = sorted(Ow['calls']); cc = sorted(Cf['calls'])
                pairs = [(t1, t2, 'eq') for (o1, t1), (o2, t2) in zip(oc, cc)]
                ratio = 1.0
            else:
                pairs, ratio = aligned_calls(Ow, Cf)
                if ratio < min_ratio:
                    continue
            for t_o, t_c, tag in pairs:
                if t_o in O and t_c in C and t_o not in cp:
                    cp[t_o] = (t_c, f'via {st:#x}' + ('' if how == 'match' else f' r={ratio:.2f}'))
                    nxt.append(t_o)
        frontier = nxt
    return cp
