#!/usr/bin/env python3
"""Recompute official memberships and bounded caller diagnostics for two fresh ELFs."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import struct
import sys

TARGETS = {
    0x13b9b8: ('pump_recovered::buy_v2::buy_handler',) * 2,
    0x13f630: ('pump_recovered::buy_v2::buy_exact_quote_in_handler',) * 2,
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
    ap.add_argument('--control', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--objdump', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / 'reconstruction/harness'))
    import score
    import win
    score.OBJDUMP = win.OBJDUMP = str(a.objdump.resolve())
    original = (score.BASE / 'original.so').read_bytes()
    os = score.sections(original)
    windows = {w['start']: w for w in score.original_windows()}
    original_map = {s: (w['bytes'], '') for s, w in windows.items()}

    def edges(blob, secs, start, size, mapping):
        raw = score.body(blob, secs, start, size)
        result = []
        off = 0
        while off < len(raw):
            op, regs, _, imm = struct.unpack_from('<BBhi', raw, off)
            if op == 0x85:
                if regs >> 4 != 1 or imm == -1:
                    result.append(['syscall', imm])
                else:
                    target = start + off + 8 + imm * 8
                    n, _ = mapping[target]
                    body = score.body(blob, secs, target, n)
                    result.append([n, digest(score.normalize(body, target, secs))])
            off += 16 if op == 0x18 else 8
        return result

    analyses = []
    for which, path in enumerate((a.control, a.candidate)):
        blob = path.read_bytes()
        secs = score.sections(blob)
        funcs = score.candidate_functions(path)
        mapping = {s: (n, sym) for s, n, sym in funcs}
        matches = score.score(path)
        rows = {}
        for start, names in TARGETS.items():
            picked = [(s, n) for s, n, sym in funcs if win.demangle(sym) == names[which]]
            if len(picked) != 1:
                raise ValueError(f'Expected one {names[which]}, got {len(picked)}')
            s, n = picked[0]
            raw = score.body(blob, secs, s, n)
            norm = score.normalize(raw, s, secs)
            w = windows[start]
            ot = [x[2] for x in win.insns(w['raw'], start, os)]
            ct = [x[2] for x in win.insns(raw, s, secs)]
            calls = edges(blob, secs, s, n, mapping)
            ocalls = edges(original, os, start, w['bytes'], original_map)
            rows[hex(start)] = {
                '_norm': norm, '_raw': raw, 'address': s, 'symbol': names[which], 'original_bytes': w['bytes'], 'candidate_bytes': n,
                'normalized_equal': norm == w['norm'],
                'diagnostic_ratio': round(difflib.SequenceMatcher(None, ot, ct, autojunk=False).ratio(), 6),
                'calls': calls, 'ordered_callees_equal_original': calls == ocalls,
            }
        analyses.append({
            'elf_sha256': digest(blob),
            'memberships': {field: [hex(s) for s, row in matches.items() if row[field]]
                            for field in ('normalized', 'raw')},
            'targets': rows,
        })
    control, candidate = analyses
    delta = {}
    for field in ('normalized', 'raw'):
        before, after = (set(x['memberships'][field]) for x in analyses)
        delta[field] = {'before': len(before), 'after': len(after),
                        'gains': sorted(after - before), 'losses': sorted(before - after)}
    for start in TARGETS:
        key = hex(start)
        b, c = control['targets'][key], candidate['targets'][key]
        c['ordered_callees_equal_control'] = c['calls'] == b['calls']
        before, after = b.pop('_norm'), c.pop('_norm')
        b.pop('_raw')
        candidate_raw = c.pop('_raw')
        if len(before) != len(after):
            raise ValueError('Function size changed')
        offsets = [i for i in range(0, len(after), 8) if before[i:i+8] != after[i:i+8]]
        if not offsets:
            raise ValueError('Expected a changed copy sequence')
        first, end = offsets[0], offsets[-1] + 8
        span = after[first:end]
        original_norm = windows[start]['norm']
        where = original_norm.find(span)
        if where < 0 or original_norm.find(span, where + 1) >= 0:
            raise ValueError('Changed sequence is not a unique original match')
        c['copy_sequence'] = {
            'changed_slots': len(offsets), 'span_bytes': len(span),
            'candidate_offset': hex(first), 'original_offset': hex(where),
            'original_address': hex(start + where),
            'normalized_sha256': digest(span),
            'raw_equal_original': candidate_raw[first:end] == windows[start]['raw'][where:where+len(span)],
            'control_differing_slots': sum(before[first+i:first+i+8] != span[i:i+8]
                                           for i in range(0, len(span), 8)),
            'candidate_differing_slots': 0,
        }
        for row in (b, c):
            calls = row.pop('calls')
            row['call_count'] = len(calls)
            row['ordered_callee_signatures_sha256'] = digest(json.dumps(calls, separators=(',', ':')).encode())
    passed = (all(not d['losses'] for d in delta.values()) and
              all(r['copy_sequence']['changed_slots'] == 8 and r['copy_sequence']['span_bytes'] == 64 and r['copy_sequence']['raw_equal_original']
                  for r in candidate['targets'].values()) and
              all(r['ordered_callees_equal_control'] for r in candidate['targets'].values()))
    # fastbuild writes the ordinarily stripped candidate.so beside unstripped.so.
    stripped = [path.with_name('candidate.so').read_bytes() for path in (a.control, a.candidate)]
    text_sections = [score.sections(blob)['.text'] for blob in stripped]
    if len(stripped[0]) != len(stripped[1]) or text_sections[0] != text_sections[1]:
        raise ValueError('Stripped ELF layout changed')
    text = text_sections[1]
    ranges = []
    for key, row in candidate['targets'].items():
        if row['address'] != control['targets'][key]['address']:
            raise ValueError('Target function moved')
        first = row['address'] - text['addr'] + text['offset'] + int(row['copy_sequence']['candidate_offset'], 16)
        ranges.append((first, first + row['copy_sequence']['span_bytes']))
    changed = [i for i, (b, c) in enumerate(zip(*stripped)) if b != c]
    outside = [i for i in changed if not any(first <= i < end for first, end in ranges)]
    stripped_report = {'control_sha256': digest(stripped[0]), 'candidate_sha256': digest(stripped[1]),
                       'bytes': len(stripped[0]), 'changed_bytes': len(changed),
                       'changed_bytes_outside_copy_regions': len(outside),
                       'copy_file_ranges': [[hex(a), hex(b)] for a, b in ranges]}
    passed = passed and len(changed) == 16 and not outside
    report = {'stripped_comparison': stripped_report, 'scope': 'Static source-build comparison; no runtime execution or new full-window gain implied.',
              'original_sha256': digest(original), 'control': control, 'candidate': candidate,
              'delta': delta, 'checks_passed': passed}
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'delta': delta, 'checks_passed': passed}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
