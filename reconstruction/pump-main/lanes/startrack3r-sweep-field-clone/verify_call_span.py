#!/usr/bin/env python3
"""Replay the fixed two-image raw-call-span evidence without executing a program.

The original is an allocation capture; control/s6 are unstripped compiler outputs.
All three image hashes and the inventory/scorer bytes are checked before parsing.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def measure(args, evidence):
    files = {'original': args.original, 'control': args.control, 's6': args.s6,
             'inventory': args.inventory, 'score.py': args.harness / 'score.py'}
    data = {name: path.read_bytes() for name, path in files.items()}
    for name, raw in data.items():
        require(digest(raw) == evidence['inputs'][name]['sha256'], f'{name}: input hash differs')
    spec = importlib.util.spec_from_file_location('span_score', files['score.py'])
    score = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(score)
    score.OBJDUMP = str(args.objdump)
    os = score.sections(data['original'])
    original = {}
    for row in csv.DictReader(io.StringIO(data['inventory'].decode('utf-8')), delimiter='\t'):
        if row['program'] != 'pump' or row['variant'] != 'selected':
            continue
        start, end = int(row['original_start']), int(row['original_end'])
        require(start not in original and end > start, 'Invalid original inventory interval')
        raw = score.body(data['original'], os, start, end - start)
        require(len(raw) == end - start, 'Short original interval')
        original[start] = (end - start, raw, score.normalize(raw, start, os))
    require(len(original) == 1035, 'Incomplete original inventory')
    start = 0xa868
    size, raw, norm = original[start]
    require(size == 24 and raw[:12] == bytes.fromhex('791100000000000085100000')
            and raw[16:] == bytes.fromhex('9500000000000000'), 'Unexpected original thunk')
    target = start + 16 + struct.unpack_from('<i', raw, 12)[0] * 8
    require(target in original, 'Original callee absent from inventory')
    callee = original[target]
    expected_shape = (callee[0], digest(callee[2]))

    def functions(blob, sections, rows):
        physical = defaultdict(list)
        for address, length, name in rows:
            physical[(address, length)].append(name)
        result = []
        for (address, length), names in sorted(physical.items()):
            body = score.body(blob, sections, address, length)
            require(length > 0 and len(body) == length, 'Short function body')
            normalized = score.normalize(body, address, sections)
            result.append({'start': address, 'bytes': length, 'raw': body,
                           'shape': (length, digest(normalized)), 'names': sorted(names)})
        return result

    ofs = functions(data['original'], os, [(s, v[0], '') for s, v in original.items()])

    def partition(fs, low, high):
        selected = [f for f in fs if low <= f['start'] < high]
        cursor = low
        for f in selected:
            require(f['start'] == cursor and cursor + f['bytes'] <= high,
                    'Call span has a gap, overlap or crossing function')
            cursor += f['bytes']
        require(cursor == high, 'Incomplete call-span partition')
        return selected, Counter(f['shape'] for f in selected)

    osp, oc = partition(ofs, start, target)
    full_original = Counter(f['shape'] for f in ofs)
    report = {'original': {'thunk_start': hex(start), 'thunk_raw': raw.hex(),
              'callee_start': hex(target), 'callee_bytes': callee[0],
              'callee_normalized_sha256': expected_shape[1], 'span_bytes': target - start,
              'physical_functions_in_span': len(osp), 'gap_bytes': 0}, 'images': {}}
    sets = {}
    for label in ['control', 's6']:
        blob = data[label]; sections = score.sections(blob)
        fs = functions(blob, sections, score.candidate_functions(files[label]))
        at = defaultdict(list)
        by_shape = defaultdict(list)
        for f in fs:
            at[f['start']].append(f)
            by_shape[f['shape']].append(f)
        all_matches = []
        bound = []
        for f in by_shape[(size, digest(norm))]:
            to = f['start'] + 16 + struct.unpack_from('<i', f['raw'], 12)[0] * 8
            choices = at[to]
            agrees = any(g['shape'] == expected_shape for g in choices)
            row = {'start': hex(f['start']), 'names': f['names'], 'raw': f['raw'].hex(),
                   'raw_equal': f['raw'] == raw, 'call_target': hex(to),
                   'callee_matches_original': agrees,
                   'callee_choices': [{'bytes': g['bytes'], 'normalized_sha256': g['shape'][1],
                                       'names': g['names']} for g in choices]}
            all_matches.append(row)
            if agrees:
                bound.append((f, to))
        require(len(bound) == 1, f'{label}: thunk/callee binding is ambiguous')
        f, to = bound[0]
        sp, cc = partition(fs, f['start'], to)
        common = oc & cc
        full_candidate = Counter(g['shape'] for g in fs)
        shared = set(full_original) & set(full_candidate)
        # Body multiplicity, rather than guessed names, accounts for boundary changes.
        crossings = []
        for shape in sorted(shared):
            delta = cc[shape] - oc[shape]
            if not delta:
                continue
            occurrences = {}
            for key, group in [('original', ofs), ('candidate', fs)]:
                occurrences[key] = [{'start': hex(g['start']), 'names': g['names']}
                                    for g in group if g['shape'] == shape]
            crossings.append({'bytes': shape[0], 'normalized_sha256': shape[1],
                              'original_span_count': oc[shape], 'candidate_span_count': cc[shape],
                              'original_total_count': full_original[shape],
                              'candidate_total_count': full_candidate[shape],
                              'span_byte_delta': delta * shape[0], 'occurrences': occurrences})
        unmatched_original = [g for g in osp if g['shape'] not in full_candidate]
        unmatched_candidate = [g for g in sp if g['shape'] not in full_original]
        code_delta = sum(g['bytes'] for g in unmatched_candidate) - sum(g['bytes'] for g in unmatched_original)
        boundary_delta = sum(r['span_byte_delta'] for r in crossings)
        span_delta = to - f['start'] - (target - start)
        require(code_delta + boundary_delta == span_delta, 'Unaccounted call-span bytes')
        norm_set, raw_set = set(), set()
        for st, (width, body, normalized) in original.items():
            matches = by_shape.get((width, digest(normalized)), [])
            if matches:
                norm_set.add(st)
            if any(g['raw'] == body for g in matches):
                raw_set.add(st)
        sets[label] = (norm_set, raw_set)
        def describe(group):
            return [{'start': hex(g['start']), 'bytes': g['bytes'], 'names': g['names']} for g in group]
        report['images'][label] = {'sha256': digest(blob), 'bytes': len(blob),
            'normalized_windows': len(norm_set), 'raw_windows': len(raw_set),
            'all_normalized_thunks': all_matches, 'bound_thunk_start': hex(f['start']),
            'bound_callee_start': hex(to), 'span_bytes': to - f['start'], 'span_delta': span_delta,
            'physical_functions_in_span': len(sp), 'gap_bytes': 0,
            'common_function_count': sum(common.values()),
            'common_function_bytes': sum(width * count for (width, _), count in common.items()),
            'unmatched_original': describe(unmatched_original), 'unmatched_candidate': describe(unmatched_candidate),
            'unmatched_function_byte_delta': code_delta, 'boundary_shapes': crossings,
            'boundary_byte_delta': boundary_delta}
    report['membership'] = {key: {'gains': [hex(a) for a in sorted(sets['s6'][i] - sets['control'][i])],
                                  'losses': [hex(a) for a in sorted(sets['control'][i] - sets['s6'][i])]}
                            for i, key in enumerate(['normalized', 'raw'])}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['original', 'inventory', 'control', 's6', 'harness', 'objdump']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=Path(__file__).with_name('RAW-CALL-SPAN.json'))
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_bytes())
    report = measure(args, evidence)
    require(report == evidence['measured'], 'Measured span evidence differs')
    print(json.dumps({'result': 'PASS', 'images': {k: {p: v[p] for p in
          ['sha256', 'normalized_windows', 'raw_windows', 'span_delta',
           'unmatched_function_byte_delta', 'boundary_byte_delta']}
          for k, v in report['images'].items()}, 'membership': report['membership']}, indent=2))


if __name__ == '__main__':
    main()
