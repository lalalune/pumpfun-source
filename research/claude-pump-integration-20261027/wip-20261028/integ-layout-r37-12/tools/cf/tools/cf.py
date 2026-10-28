#!/usr/bin/env python3
"""coordfiles analysis library: original windows / candidate functions with Source sites,
error codes, coordinate-masked shapes and call edges."""
import hashlib, json, re, struct, sys, pickle, os
from collections import defaultdict, Counter
from pathlib import Path

SC = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
sys.path.insert(0, str(SC / 'harness'))
from score import sections, body, normalize, original_windows, candidate_functions, BASE  # noqa
from coords import sites  # noqa
from win import demangle  # noqa

PREFIX = 'programs/pump/src/'


def insn_offsets(raw):
    out, i = [], 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        out.append((i, n)); i += n
    return out


def call_edges(raw, start):
    out = []
    for off, n in insn_offsets(raw):
        if raw[off] == 0x85 and raw[off + 1] >> 4 == 1:
            imm = struct.unpack_from('<i', raw, off + 4)[0]
            if imm != -1:
                out.append((off, start + off + 8 + imm * 8))
    return out


def site_code(raw, ls):
    """error code stored near the line slot (stw imm in [100, 0x10000))."""
    if ls is None:
        return None
    best = None
    for off, n in insn_offsets(raw):
        if abs(off - ls) > 96 or off == ls or raw[off] != 0x62:
            continue
        imm = struct.unpack_from('<i', raw, off + 4)[0]
        if 100 <= imm < 0x10000 and (best is None or abs(off - ls) < best[0]):
            best = (abs(off - ls), imm)
    return best[1] if best else None


def shape(norm, sl):
    b = bytearray(norm)
    for s in sl:
        for k in (s['len_slot'], s['line_slot']):
            if k is not None:
                b[k + 4:k + 8] = bytes(4)
    return hashlib.sha1(bytes(b)).hexdigest()[:16]


def load_side(blob, secs, items):
    out = {}
    for start, raw, norm, name in items:
        sl = sites(blob, secs, start, raw)
        sl.sort(key=lambda s: s['len_slot'])
        for s in sl:
            s['code'] = site_code(raw, s['line_slot'])
            s['short'] = s['path'][len(PREFIX):] if s['path'].startswith(PREFIX) else s['path']
        out[start] = {'start': start, 'bytes': len(raw), 'raw': raw, 'norm': norm, 'name': name,
                      'sites': sl, 'calls': call_edges(raw, start), 'shape': shape(norm, sl),
                      'hash': hashlib.sha256(norm).digest()}
    return out


_OCACHE = SC / 'lanes/integ-layout/work/cf_orig_side.pkl'


def load_orig():
    if _OCACHE.exists():
        return pickle.loads(_OCACHE.read_bytes())
    ob = (BASE / 'original.so').read_bytes(); osec = sections(ob)
    O = load_side(ob, osec, [(w['start'], w['raw'], w['norm'], None) for w in original_windows()])
    _OCACHE.write_bytes(pickle.dumps(O))
    return O


def load_cand(cand):
    cb = Path(cand).read_bytes(); cs = sections(cb)
    items = []
    for s, n, nm in candidate_functions(cand):
        raw = body(cb, cs, s, n)
        items.append((s, raw, normalize(raw, s, cs), demangle(nm)))
    return load_side(cb, cs, items)


def matched_map(O, C):
    byhash = defaultdict(list)
    for a, f in C.items():
        byhash[(f['bytes'], f['hash'])].append(a)
    return {st: byhash[(w['bytes'], w['hash'])] for st, w in O.items() if (w['bytes'], w['hash']) in byhash}


def callers(side):
    d = defaultdict(list)
    for st, w in side.items():
        for off, t in w['calls']:
            d[t].append((st, off))
    return d


def fmt_sites(sl):
    return ' '.join(f"{s['short']}:{s['line']}({s['code']})" for s in sl)
