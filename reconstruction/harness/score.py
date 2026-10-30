#!/usr/bin/env python3
"""Score a main-Pump candidate exactly like the Codex inventory (inventory_current.py).

A window (functions.tsv, program=pump, variant=selected) is matched when some candidate
function symbol has the same length and identical bytes after masking ONLY internal
direct-call immediates (op 0x85, src=1, imm!=-1) and lddw values pointing inside an ELF
section. Raw matches are counted separately.

Usage: score.py <unstripped.so> [--baseline score.json | --no-baseline] [--json out.json] [--quiet]
Prints counts and gains/losses vs the baseline (default: pump-main/baseline/score.json).
A missing baseline file is an error: gains/losses against an empty baseline would report
every matched window as a gain and no losses. Pass --no-baseline to score without one.
"""
import argparse, csv, hashlib, json, re, struct, subprocess, sys, tempfile
from pathlib import Path
from llvm_tools import objdump
from functools import lru_cache
import io

H = Path(__file__).resolve().parent
SC = H.parent
BASE = SC / 'base'
DEFAULT_BASELINE = SC / 'pump-main/baseline/score.json'


from score_admission import sections, baseline as load_baseline, same_domain, report_destination


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
    from elf_symbols import function_symbols
    return function_symbols(Path(path).read_bytes())


@lru_cache(maxsize=2)
def _window_rows(orig, inventory):
    """Cache immutable rows by input bytes, never by timestamps or a saved pickle."""
    os_ = sections(orig)
    reader = csv.DictReader(io.StringIO(inventory), delimiter='\t')
    required = {'program', 'variant', 'original_start', 'original_end'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('window inventory is missing required columns')
    rows = []
    seen = set()
    text = os_['.text']
    for r in reader:
        if r['program'] != 'pump' or r['variant'] != 'selected':
            continue
        start, end = int(r['original_start']), int(r['original_end'])
        if (start in seen or start % 8 or end % 8 or end <= start
                or start < text['addr'] or end > text['addr'] + text['size']):
            raise ValueError(f'invalid or duplicate selected window: {start}:{end}')
        seen.add(start)
        raw = body(orig, os_, start, end - start)
        if len(raw) != end - start:
            raise ValueError(f'truncated selected window: {start}:{end}')
        rows.append((start, end - start, raw, normalize(raw, start, os_)))
    if not rows:
        raise ValueError('window inventory contains no selected Pump windows')
    return tuple(rows)


def original_windows():
    orig = (BASE / 'original.so').read_bytes()
    inventory = (BASE / 'functions.tsv').read_text(encoding='utf-8')
    # Return fresh containers so an analysis consumer cannot poison later scores.
    return [dict(zip(('start', 'bytes', 'raw', 'norm'), row))
            for row in _window_rows(orig, inventory)]


def score(cand_path):
    """Return window memberships, preserving the existing library interface."""
    return score_with_hash(cand_path)[0]


def score_with_hash(cand_path):
    """Score one byte snapshot and return its memberships and SHA-256.

    The external symbol reader must see the same bytes as normalization, even if
    another build replaces the supplied path. The private copy is removed on
    success or failure. This binds the result to bytes read, not source provenance.
    """
    cand = Path(cand_path).read_bytes(); cs = sections(cand)
    with tempfile.TemporaryDirectory(prefix='pump-score-') as temporary:
        snapshot = Path(temporary) / 'candidate.so'
        snapshot.write_bytes(cand)
        funcs = candidate_functions(snapshot)
    by = {}
    for start, length, name in funcs:
        raw = body(cand, cs, start, length)
        by.setdefault((length, hashlib.sha256(normalize(raw, start, cs)).digest()), []).append((start, name, raw))
    res = {}
    for w in original_windows():
        ms = by.get((w['bytes'], hashlib.sha256(w['norm']).digest()), [])
        res[w['start']] = {'normalized': bool(ms), 'raw': any(m[2] == w['raw'] for m in ms),
                           'symbols': [m[1] for m in ms], 'bytes': w['bytes']}
    return res, hashlib.sha256(cand).hexdigest()




def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('--baseline', type=Path, default=DEFAULT_BASELINE)
    ap.add_argument('--no-baseline', action='store_true', help='report counts only; gains/losses are relative to an empty baseline')
    ap.add_argument('--json', type=Path)
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()
    if a.no_baseline:
        base = None
    elif a.baseline.is_file():
        base = load_baseline(a.baseline)
    else:
        print(f'score.py: baseline not found: {a.baseline} (pass --no-baseline to score without one)', file=sys.stderr)
        sys.exit(2)
    inputs = [a.candidate, BASE / 'original.so', BASE / 'functions.tsv']
    if base is not None:
        inputs.insert(1, a.baseline)
    report_destination(a.json, inputs)
    cur, candidate_sha256 = score_with_hash(a.candidate)
    if base is None:
        base = {}
    else:
        same_domain(cur, base)
    n = sum(v['normalized'] for v in cur.values()); r = sum(v['raw'] for v in cur.values())
    tb = sum(v['bytes'] for v in cur.values() if v['normalized'])
    gains = sorted(k for k, v in cur.items() if v['normalized'] and not base.get(k, {}).get('normalized'))
    losses = sorted(k for k, v in cur.items() if not v['normalized'] and base.get(k, {}).get('normalized'))
    rg = sorted(k for k, v in cur.items() if v['raw'] and not base.get(k, {}).get('raw'))
    rl = sorted(k for k, v in cur.items() if not v['raw'] and base.get(k, {}).get('raw'))
    summary = {'candidate_sha256': candidate_sha256,
               'normalized': n, 'raw': r, 'total': len(cur), 'matched_text_bytes': tb,
               'gains': [hex(x) for x in gains], 'losses': [hex(x) for x in losses],
               'raw_gains': [hex(x) for x in rg], 'raw_losses': [hex(x) for x in rl]}
    if a.json:
        a.json.write_text(json.dumps({'summary': summary, 'windows': {str(k): v for k, v in cur.items()}}, indent=1))
    print(json.dumps(summary, indent=None if a.quiet else 1))


if __name__ == '__main__':
    main()
