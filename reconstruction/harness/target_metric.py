#!/usr/bin/env python3
"""Measure how close a candidate build is to one original window.

  target_metric.py <unstripped.so> <orig_start> [<orig_start> ...] [--sym REGEX] [--top N] [--slots N]

For each candidate function (those whose symbol matches --sym, else the closest by
  opcode n-grams) prints one JSON line: size, normalized/raw equality, the instruction
  ratio used by win.py, the differing normalized 8-byte slots when sizes are equal, and
  named direct, syscall-or-relocated and indirect-call counts. Lower `slots_diff` and
  higher `ratio` mean closer; only score.py decides acceptance.
"""
import argparse
import copy
import difflib
import json
import re
import struct
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
from score import sections, normalize, body, candidate_functions, original_windows  # noqa: E402
from win import Cand, insns, demangle, best_candidates, ORIG, ORIG_SECS  # noqa: E402
from instruction_stream import decode_instructions, instruction_offsets
from compare_scores import publish_report
from collections import Counter


def decode(raw, offset):
    width = 16 if raw[offset] == 0x18 else 8
    row = decode_instructions(raw[offset:offset + width])[0]
    return {key: row[key] for key in ('opcode', 'dst', 'src', 'displacement', 'immediate')}


def field_differences(original, candidate, limit=12):
    """Inputs must already use score.normalize; never align LDDW payloads as opcodes."""
    if limit < 0:
        raise ValueError('limit must be nonnegative')
    left, right = list(instruction_offsets(original)), list(instruction_offsets(candidate))
    if len(original) != len(candidate) or left != right:
        return {'comparable': False, 'reason': 'instruction boundaries or byte lengths differ'}
    counts, rows = Counter(), []
    for offset in left:
        a, b = decode(original, offset), decode(candidate, offset)
        fields = {key: {'original': a[key], 'candidate': b[key]} for key in a if a[key] != b[key]}
        # Preserve visibility of changed reserved LDDW continuation fields.
        if original[offset] == candidate[offset] == 0x18 and original[offset+8:offset+12] != candidate[offset+8:offset+12]:
            fields['lddw_reserved'] = {'original': original[offset+8:offset+12].hex(),
                                       'candidate': candidate[offset+8:offset+12].hex()}
        counts.update(fields.keys())
        if fields and len(rows) < limit:
            rows.append({'offset': offset, 'fields': fields})
    return {'comparable': True, 'field_counts': dict(sorted(counts.items())), 'first_differences': rows}


def call_counts(raw):
    counts = {'internal': 0, 'syscall_or_relocated': 0, 'indirect': 0}
    for i in instruction_offsets(raw):
        op = raw[i]
        if op == 0x8D:
            counts['indirect'] += 1
        elif op == 0x85:
            imm = struct.unpack_from('<i', raw, i + 4)[0]
            if raw[i + 1] >> 4 == 1 and imm != -1:
                counts['internal'] += 1
            else:
                counts['syscall_or_relocated'] += 1
    return counts


def calls(raw):
    """Return the legacy direct/syscall-or-relocated tuple."""
    counts = call_counts(raw)
    return counts['internal'], counts['syscall_or_relocated']


def measure_window(w, cand, pattern=None, top=3, slots=12):
    """Measure one window while sharing the loaded candidate across a batch."""
    start = w['start']
    if pattern:
        picks = [(s, n, nm) for s, n, nm in cand.funcs if pattern.search(nm) or pattern.search(demangle(nm))]
    else:
        picks = [(s, n, nm) for _, _, s, n, nm in best_candidates(w, cand, top)]
    otok = [x[2] for x in insns(w['raw'], start, ORIG_SECS)]
    ocalls = call_counts(w['raw'])
    rows = []
    measured = {}
    for s, n, nm in picks:
        if (s, n) in measured:
            row = copy.deepcopy(measured[s, n])
            row['symbol'] = demangle(nm)
            rows.append(row)
            continue
        raw = cand.fn(s, n)
        ccalls = call_counts(raw)
        norm = normalize(raw, s, cand.secs)
        ctok = [x[2] for x in insns(raw, s, cand.secs)]
        row = {'window': hex(start), 'window_bytes': w['bytes'], 'symbol': demangle(nm), 'cand_start': hex(s), 'cand_bytes': n,
               'normalized_equal': norm == w['norm'], 'raw_equal': raw == w['raw'],
               'ratio': round(difflib.SequenceMatcher(None, otok, ctok, autojunk=False).ratio(), 5),
               'calls_original': (ocalls['internal'], ocalls['syscall_or_relocated']),
               'calls_candidate': (ccalls['internal'], ccalls['syscall_or_relocated']),
               'call_counts_original': ocalls, 'call_counts_candidate': ccalls}
        row['normalized_field_differences'] = field_differences(w['norm'], norm, slots)
        if n == w['bytes']:
            diff = [i for i in range(0, n, 8) if norm[i:i + 8] != w['norm'][i:i + 8]]
            row['slots_diff'] = len(diff)
            row['first_diff_offsets'] = [hex(i) for i in diff[:slots]]
        measured[s, n] = row
        rows.append(row)
    rows.sort(key=lambda r: (-r['normalized_equal'], r.get('slots_diff', 1 << 30), -r['ratio']))
    return rows[:top] if pattern is None else rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidate', type=Path)
    ap.add_argument('start', nargs='+', type=lambda value: int(value, 0), help='one or more original window addresses')
    ap.add_argument('--sym', help='regex over mangled or demangled candidate symbols')
    ap.add_argument('--top', type=int, default=3)
    ap.add_argument('--slots', type=int, default=12)
    ap.add_argument('--json', type=Path, help='also save all rows as one JSON array')
    a = ap.parse_args(argv)
    if a.top <= 0 or a.slots < 0:
        ap.error('--top must be positive and --slots must be nonnegative')
    try:
        pattern = re.compile(a.sym) if a.sym is not None else None
    except re.error as error:
        ap.error(f'invalid symbol regex: {error}')
    starts = list(dict.fromkeys(a.start))
    try:
        windows = {w['start']: w for w in original_windows()}
    except (OSError, ValueError, KeyError, struct.error) as error:
        ap.error(f'cannot load original windows: {error}')
    missing = [hex(start) for start in starts if start not in windows]
    if missing:
        ap.error('unknown original windows: ' + ', '.join(missing))
    try:
        cand = Cand(a.candidate)
        rows = []
        for start in starts:
            measured = measure_window(windows[start], cand, pattern, a.top, a.slots)
            if pattern is None and not measured:
                ap.error(f'no candidate function for window {start:#x} in the ranked search scope')
            rows.extend(measured)
    except (OSError, ValueError, KeyError, struct.error) as error:
        ap.error(f'cannot measure candidate: {error}')
    if pattern is not None and not rows:
        ap.error('explicit --sym did not select any candidate function')
    if a.json:
        try:
            publish_report(a.json, json.dumps(rows, indent=2) + '\n')
        except OSError as error:
            ap.error(f'cannot create diagnostic report: {error}')
    for row in rows:
        print(json.dumps(row))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
