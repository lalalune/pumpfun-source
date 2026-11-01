#!/usr/bin/env python3
"""Annotated event map of admin_cto::execute (original 0x22a10 or a candidate build).

  annotate.py orig                      # original window, events only
  annotate.py cand <unstripped.so>      # candidate admin_cto::execute, events only
  annotate.py ... --full                # every instruction, with annotations

Events: direct calls (callee resolved by normalized body hash + size to candidate names; the
original's callees are all matched windows), syscalls, rodata string loads (log literals),
Source{file,line} sites, error-code immediates (stw of 6000..6999 / 2000..4100), exits.
Diagnostic only.
"""
import argparse, hashlib, re, struct, sys
from collections import defaultdict
from pathlib import Path

H = Path('./worktrees/restore/reconstruction/harness')
sys.path.insert(0, str(H))
from score import sections, normalize, body, candidate_functions, original_windows, BASE  # noqa
from win import demangle  # noqa
from coords import sites  # noqa

DEF_CAND = Path.home() / '.cache/pumpfun-reconstruction/lanes/admincto-reconstruction/out/base/unstripped.so'
SYSCALLS = {}


def decode(raw, addr):
    out = []; i = 0
    while i < len(raw):
        op = raw[i]
        if op == 0x18:
            lo = struct.unpack_from('<I', raw, i + 4)[0]; hi = struct.unpack_from('<I', raw, i + 12)[0]
            out.append((addr + i, op, raw[i + 1], 0, lo | hi << 32)); i += 16
        else:
            _, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
            out.append((addr + i, op, regs, off, imm)); i += 8
    return out


def rodata_str(blob, secs, v):
    for n, s in secs.items():
        if s['addr'] and s['addr'] <= v < s['addr'] + s['size'] and n in ('.rodata',):
            o = v - s['addr'] + s['offset']
            b = blob[o:o + 90]
            m = re.match(rb'[\x20-\x7e]{6,}', b)
            if m:
                return m.group(0).decode()
    return None


def hkey(blob, secs, s, n):
    return (n, hashlib.sha256(normalize(body(blob, secs, s, n), s, secs)).hexdigest())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('which', choices=['orig', 'cand'])
    ap.add_argument('cand', nargs='?', type=Path, default=DEF_CAND)
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--sym', default=r'admin_cto::execute$')
    a = ap.parse_args()
    cblob = a.cand.read_bytes(); csecs = sections(cblob)
    cf = candidate_functions(a.cand)
    cnames = defaultdict(list); csize = {}
    for s, n, nm in cf:
        cnames[s].append(demangle(nm)); csize[s] = n
    byhash = defaultdict(set)
    for s, n in csize.items():
        for nm in cnames[s]:
            byhash[hkey(cblob, csecs, s, n)].add(re.sub(r'pump_recovered::', '', nm))
    if a.which == 'orig':
        oblob = (BASE / 'original.so').read_bytes(); osecs = sections(oblob)
        wins = {w['start']: w['bytes'] for w in original_windows()}
        start = 0x22a10; size = wins[start]; blob, secs = oblob, osecs

        def name(t):
            if t not in wins:
                return '?%x' % t
            ns = byhash.get(hkey(oblob, osecs, t, wins[t]))
            return ' | '.join(sorted(ns))[:120] if ns else 'UNMATCHED:%x' % t
    else:
        cands = [s for s in csize if any(re.search(a.sym, x) for x in cnames[s])]
        start = cands[0]; size = csize[start]; blob, secs = cblob, csecs

        def name(t):
            return ' | '.join(sorted(set(re.sub(r'pump_recovered::', '', x) for x in cnames.get(t, ['?%x' % t]))))[:120]
    raw = body(blob, secs, start, size)
    src = {s['line_slot']: s['line'] for s in sites(blob, secs, start, raw) if s['line_slot'] is not None}
    ins = decode(raw, start)
    print('# %s start=0x%x bytes=%d' % (a.which, start, size))
    for pc, op, regs, off, imm in ins:
        rel = pc - start
        ann = []
        if op == 0x85:
            if regs >> 4 == 1 and imm != -1:
                ann.append('CALL ' + name(pc + 8 + imm * 8))
            else:
                ann.append('SYSCALL %x' % (imm & 0xffffffff))
        elif op == 0x18:
            s = rodata_str(blob, secs, imm)
            if s and not s.endswith('.rs'):
                ann.append('STR "%s"' % s[:70])
        elif op == 0x95:
            ann.append('EXIT')
        if rel in src:
            ann.append('LINE %d' % src[rel])
        if op in (0x62, 0x7a, 0xb7, 0xb4) and (6000 <= imm < 6300 or 2000 <= imm < 4200) and not (rel in src):
            ann.append('imm %d' % imm)
        if a.full or ann:
            txt = '%02x r%d r%d off=%d imm=%d' % (op, regs & 15, regs >> 4, off, imm)
            print('%06x  %-34s %s' % (rel, txt if a.full else '', '; '.join(ann)))


if __name__ == '__main__':
    main()
