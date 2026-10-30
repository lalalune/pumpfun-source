#!/usr/bin/env python3
"""Measure exact byte gaps without treating size similarity as source completeness.

The chosen snapshot is explicit. Missing current-status files are reported as
missing rather than silently replaced by a historical candidate. This only reads
artifacts; it neither compiles nor executes contract code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from analyze import elf_layout
from compare import compare

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def header(raw):
    layout = elf_layout(raw)
    return {key: layout[key] for key in ('machine', 'flags', 'entry', 'elf_extent',
                                        'allocation_bytes', 'trailing_bytes',
                                        'trailing_all_zero', 'elf_sha256')}


def sections(raw):
    result = {}
    for entry in elf_layout(raw)['sections']:
        # SHT_NOBITS occupies memory but no file bytes.
        payload = b'' if entry['type'] == 8 else raw[entry['offset']:entry['offset'] + entry['size']]
        assert entry['name'] not in result, 'Duplicate section name requires index-based comparison'
        result[entry['name']] = dict(entry, sha256=sha(payload), payload=payload)
    return result


def measure(original, candidate):
    a, b = elf_layout(original), elf_layout(candidate)
    left, right = sections(original), sections(candidate)
    rows = []
    for name in sorted(set(left) | set(right)):
        x, y = left.get(name), right.get(name)
        row = {'section': name, 'original_present': x is not None, 'candidate_present': y is not None}
        for label, item in [('original', x), ('candidate', y)]:
            row[label] = {k: v for k, v in item.items() if k != 'payload'} if item else None
        if x is not None and y is not None:
            row['file_payload_comparison'] = compare(x['payload'], y['payload'])
        rows.append(row)
    return {'allocation_comparison': compare(original, candidate),
            'raw_elf_comparison': compare(original[:a['elf_extent']], candidate[:b['elf_extent']]),
            'original_header': header(original), 'candidate_header': header(candidate),
            'sections': rows,
            'source_completeness_inferred': False,
            'historical_compiler_identity_proven': False,
            'note': 'Equal section sizes, matching instructions and finite behavior tests do not prove whole source or historical build identity.'}


def read(root, name, inputs):
    path = root / name
    data = path.read_bytes()
    inputs[name] = sha(data)
    return data


def audit(root, index_path):
    inputs = {}
    status = json.loads(read(root, 'repro/status.json', inputs))
    index = json.loads(read(root, index_path, inputs))
    snapshot = {}
    for name, entry in index['programs'].items():
        original = read(root, entry['original_path'], inputs)
        candidate_path = entry['candidate_path']
        if not (root / candidate_path).is_file():
            snapshot[name] = {'error': 'snapshot_candidate_missing', 'candidate_path': candidate_path}
            continue
        candidate = read(root, candidate_path, inputs)
        assert sha(original) == entry['original_sha256'], name
        assert sha(candidate) == entry['candidate_sha256'], name
        snapshot[name] = {'candidate_path': candidate_path, 'original_path': entry['original_path'],
                          **measure(original, candidate)}
    status_health = {}
    for name, entry in status.items():
        candidate = entry.get('candidate_artifact')
        comparison = entry.get('comparison_report')
        current = {'candidate_path': candidate, 'candidate_exists': bool(candidate and (root / candidate).is_file()),
                   'comparison_path': comparison, 'comparison_exists': bool(comparison and (root / comparison).is_file())}
        if current['candidate_exists']:
            binary = read(root, candidate, inputs)
            current['candidate_sha256'] = sha(binary)
        if current['comparison_exists']:
            build = json.loads(read(root, comparison, inputs))
            current['selected_toolchain'] = build.get('selected_toolchain')
            current['candidate_matches_build_report'] = current.get('candidate_sha256') == build['comparison']['candidate_sha256']
            missing, different = [], []
            for source, expected in build['source_sha256'].items():
                if not (root / source).is_file():
                    missing.append(source)
                elif sha(read(root, source, inputs)) != expected:
                    different.append(source)
            current['missing_compiler_inputs'] = missing
            current['different_compiler_inputs'] = different
        status_health[name] = current
    result = {'scope': 'Static exact-byte and source-binding audit. No deployment, runtime, exhaustiveness or compiler-identity proof.',
              'snapshot_index': index_path, 'snapshot_programs': snapshot,
              'current_status_health': status_health,
              'input_sha256': dict(sorted(inputs.items()))}
    try:
        result['repository_revision'] = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        result['repository_revision'] = None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--index', required=True, help='Repository-relative current-analysis-index.json of an explicitly selected pass')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve prior audits; choose a fresh output file'
    result = audit(args.repo.resolve(), args.index)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'snapshot_programs': len(result['snapshot_programs']),
                      'exact_allocations': [name for name, row in result['snapshot_programs'].items()
                                            if row.get('allocation_comparison', {}).get('full_byte_equality')],
                      'missing_status_candidates': [name for name, row in result['current_status_health'].items()
                                                    if not row['candidate_exists']]}, indent=2))


if __name__ == '__main__':
    main()
