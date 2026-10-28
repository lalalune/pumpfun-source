#!/usr/bin/env python3
"""Analysis helpers for the coordlib lane: original windows + candidate functions, call graphs, Source sites."""
import hashlib, json, pickle, re, struct, subprocess, sys
from collections import defaultdict
from pathlib import Path

SC = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
sys.path.insert(0, str(SC / 'harness'))
from score import sections, body, normalize, original_windows, candidate_functions, BASE  # noqa
from coords import read_cstr_at  # noqa
import sites2 as _sites2  # nearest-store decoder (coords.sites can take a neighbouring site's line/code)


def sites(blob, secs, start, raw):
    return _sites2.sites(blob, secs, start, raw, read_cstr_at)

OBJDUMP = str(Path.home() / '.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump')


def demangle(s):
    m = re.match(r'^_ZN(.*)E$', s)
    if not m:
        return s
    rest, parts = m.group(1), []
    while rest and rest[0].isdigit():
        n = re.match(r'^(\d+)', rest).group(1); rest = rest[len(n):]
        parts.append(rest[:int(n)]); rest = rest[int(n):]
    if parts and re.fullmatch(r'h[0-9a-f]{16}', parts[-1]):
        parts = parts[:-1]
    t = '::'.join(parts)
    for a, b in [('$LT$', '<'), ('$GT$', '>'), ('$RF$', '&'), ('$BP$', '*'), ('$C$', ','), ('$u20$', ' '),
                 ('$u27$', "'"), ('$u5b$', '['), ('$u5d$', ']'), ('$u7b$', '{'), ('$u7d$', '}'), ('$u3b$', ';'),
                 ('$u2b$', '+'), ('$u22$', '"'), ('$LP$', '('), ('$RP$', ')'), ('..', '::'), ('$u7e$', '~')]:
        t = t.replace(a, b)
    return t


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
    """error code stored near the line slot (stw imm in 100..0xffff)."""
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
        out[start] = {'start': start, 'bytes': len(raw), 'raw': raw, 'norm': norm, 'name': name,
                      'sites': sl, 'calls': call_edges(raw, start), 'shape': shape(norm, sl),
                      'hash': hashlib.sha256(norm).digest()}
    return out


_O = None


def load_orig():
    global _O
    if _O is None:
        cache = SC / 'lanes/integ-layout/work/cl_orig_side_v2.pkl'
        if cache.exists():
            _O = pickle.loads(cache.read_bytes())
        else:
            ob = (BASE / 'original.so').read_bytes(); osec = sections(ob)
            _O = load_side(ob, osec, [(w['start'], w['raw'], w['norm'], None) for w in original_windows()])
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(pickle.dumps(_O))
    return _O


def load_cand(cand):
    cb = Path(cand).read_bytes(); cs = sections(cb)
    items = []
    for s, n, nm in candidate_functions(cand):
        raw = body(cb, cs, s, n)
        items.append((s, raw, normalize(raw, s, cs), demangle(nm)))
    return load_side(cb, cs, items)


def matches(O, C):
    byhash = defaultdict(list)
    for a, f in C.items():
        byhash[(f['bytes'], f['hash'])].append(a)
    return {st: byhash[(w['bytes'], w['hash'])] for st, w in O.items() if (w['bytes'], w['hash']) in byhash}


def callers(side):
    r = defaultdict(list)
    for st, w in side.items():
        for off, t in w['calls']:
            r[t].append((st, off))
    return r


def objdump(path, start, end):
    txt = subprocess.check_output([OBJDUMP, '-d', '--no-show-raw-insn', f'--start-address={start:#x}', f'--stop-address={end:#x}', str(path)], text=True)
    d = []
    for line in txt.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
        if m:
            d.append((int(m.group(1), 16), re.sub(r'\s+<\.text\+0x[0-9a-f]+>', '', m.group(2).strip())))
    return d
