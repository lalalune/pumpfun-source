#!/usr/bin/env python3
"""Score a main-Pump candidate exactly like the Codex inventory (inventory_current.py).

A window (functions.tsv, program=pump, variant=selected) is matched when some candidate
function symbol has the same length and identical bytes after masking ONLY internal
direct-call immediates (op 0x85, src=1, imm!=-1) and lddw values pointing inside an ELF
section. Raw matches are counted separately.

Usage: score.py <unstripped.so> [--baseline inventory.json] [--json out.json] [--quiet]
Prints counts and gains/losses vs the baseline (default: base/current/inventory.json).
"""
import argparse, csv, hashlib, json, re, struct, subprocess, sys
from pathlib import Path
from llvm_tools import objdump

H = Path(__file__).resolve().parent
SC = H.parent
BASE = SC / 'base'


def sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hdrs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    strtab = hdrs[shstrndx]
    name = lambda off: blob[strtab[4] + off:blob.index(b'\0', strtab[4] + off)].decode()
    return {name(h[0]): {'addr': h[3], 'offset': h[4], 'size': h[5]} for h in hdrs}


def normalize(raw, address, secs):
    masked = bytearray(raw)
    i = 0
    while i < len(raw):
        op, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
        if op == 0x18:
            value = struct.unpack_from('<I', raw, i + 4)[0] | struct.unpack_from('<I', raw, i + 12)[0] << 32
            if any(s['addr'] > 0 and s['addr'] <= value < s['addr'] + s['size'] for s in secs.values()):
                masked[i + 4:i + 8] = bytes(4); masked[i + 12:i + 16] = bytes(4)
            i += 16
        else:
            if op == 0x85 and regs >> 4 == 1 and imm != -1:
                masked[i + 4:i + 8] = bytes(4)
            i += 8
    return bytes(masked)


def body(image, secs, address, size):
    t = secs['.text']
    if any(type(value) is not int or value < 0 for value in
           (address, size, t['addr'], t['offset'], t['size'])):
        raise ValueError('function and .text bounds must be nonnegative integers')
    if t['offset'] + t['size'] > len(image):
        raise ValueError('.text section extends beyond the ELF file')
    relative = address - t['addr']
    if relative < 0 or relative > t['size'] or size > t['size'] - relative:
        raise ValueError(f'function range {address:#x}+{size:#x} is outside .text')
    o = relative + t['offset']
    return image[o:o + size]


def candidate_functions(path):
    text = subprocess.check_output([objdump(), '-t', str(path)], text=True)
    funcs = []
    for line in text.splitlines():
        m = re.match(r'^([0-9a-f]+) .* F \.text\s+([0-9a-f]+)\s+(?:\.hidden\s+)?(\S+)$', line)
        if m:
            addr, size, name = int(m.group(1), 16), int(m.group(2), 16), m.group(3)
            if size:
                funcs.append((addr, size, name))
    return funcs


def original_windows():
    # Read both inputs each time: a previous inventory must not set today's
    # window set or supply bytes from a different captured original.
    orig = (BASE / 'original.so').read_bytes(); os_ = sections(orig)
    rows = []
    with (BASE / 'functions.tsv').open() as inventory:
        for r in csv.DictReader(inventory, delimiter='\t'):
            if r['program'] != 'pump' or r['variant'] != 'selected':
                continue
            s, e = int(r['original_start']), int(r['original_end'])
            raw = body(orig, os_, s, e - s)
            rows.append({'start': s, 'bytes': e - s, 'raw': raw, 'norm': normalize(raw, s, os_)})
    return rows


def score(cand_path):
    cand = Path(cand_path).read_bytes(); cs = sections(cand)
    by = {}
    for start, length, name in candidate_functions(cand_path):
        raw = body(cand, cs, start, length)
        by.setdefault((length, hashlib.sha256(normalize(raw, start, cs)).digest()), []).append((start, name, raw))
    res = {}
    for w in original_windows():
        ms = by.get((w['bytes'], hashlib.sha256(w['norm']).digest()), [])
        res[w['start']] = {'normalized': bool(ms), 'raw': any(m[2] == w['raw'] for m in ms),
                           'symbols': [m[1] for m in ms], 'bytes': w['bytes']}
    return res


def load_baseline(p):
    d = json.loads(Path(p).read_text())
    if 'windows' in d and isinstance(d['windows'], list):  # Codex inventory format
        return {w['start']: {'normalized': bool(w['normalized_matches']), 'raw': w['raw_match'], 'bytes': w['bytes']} for w in d['windows']}
    return {int(k): v for k, v in d['windows'].items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('--baseline', type=Path, default=BASE / 'current/inventory.json')
    ap.add_argument('--json', type=Path)
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    cur = score(a.candidate)
    base = load_baseline(a.baseline) if a.baseline and a.baseline.exists() else {}
    n = sum(v['normalized'] for v in cur.values()); r = sum(v['raw'] for v in cur.values())
    tb = sum(v['bytes'] for v in cur.values() if v['normalized'])
    gains = sorted(k for k, v in cur.items() if v['normalized'] and not base.get(k, {}).get('normalized'))
    losses = sorted(k for k, v in cur.items() if not v['normalized'] and base.get(k, {}).get('normalized'))
    rg = sorted(k for k, v in cur.items() if v['raw'] and not base.get(k, {}).get('raw'))
    rl = sorted(k for k, v in cur.items() if not v['raw'] and base.get(k, {}).get('raw'))
    summary = {'candidate_sha256': hashlib.sha256(a.candidate.read_bytes()).hexdigest(),
               'normalized': n, 'raw': r, 'total': len(cur), 'matched_text_bytes': tb,
               'gains': [hex(x) for x in gains], 'losses': [hex(x) for x in losses],
               'raw_gains': [hex(x) for x in rg], 'raw_losses': [hex(x) for x in rl]}
    if a.json:
        a.json.write_text(json.dumps({'summary': summary, 'windows': {str(k): v for k, v in cur.items()}}, indent=1))
    print(json.dumps(summary, indent=None if a.quiet else 1))


if __name__ == '__main__':
    main()
