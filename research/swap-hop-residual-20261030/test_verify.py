#!/usr/bin/env python3
"""Verify packet integrity and fail-closed controls, with optional real ELF replay."""
import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import textwrap
import unittest
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FILES = {'README.md', 'RESULT.json', 'analyze.py', 'test_verify.py'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON field: {key}')
        result[key] = value
    return result


def load_analyze():
    path = HERE / 'analyze.py'
    module = types.ModuleType('packet_analyze')
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


analyze = load_analyze()


def implementation_hashes():
    from instruction_stream import instruction_boundaries
    functions = {'score.normalize': analyze.score.normalize,
                 'score.body': analyze.score.body,
                 'score.sections': analyze.score.sections,
                 'score.original_windows': analyze.score.original_windows,
                 'score._window_rows': analyze.score._window_rows,
                 'elf_symbols.function_symbols': analyze.function_symbols,
                 'instruction_stream.instruction_boundaries': instruction_boundaries}
    return {name: hashlib.sha256(textwrap.dedent(inspect.getsource(fn)).encode()).hexdigest()
            for name, fn in functions.items()}


def verify_checksums(folder):
    rows = {}
    for line in (folder / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        parts = line.split()
        require(len(parts) == 2, 'invalid checksum row')
        value, name = parts
        require(name in FILES and name not in rows, 'invalid or duplicate checksum member')
        require(re.fullmatch('[0-9a-f]{64}', value), 'invalid checksum digest')
        require(digest(folder / name) == value, f'sha256 mismatch: {name}')
        rows[name] = value
    require(set(rows) == FILES, 'incomplete checksum inventory')
    entries = [p for p in folder.iterdir() if p.name != '__pycache__']
    require(all(p.is_file() and not p.is_symlink() for p in entries), 'non-regular packet entry')
    require({p.name for p in entries} == FILES | {'SHA256SUMS'}, 'unexpected packet file')


def validate_result(result):
    require(type(result.get('schema')) is int and result['schema'] == 2, 'schema')
    original = result['original']
    require(original == {'path': 'evidence/original/pump/deployed.so',
                         'sha256': analyze.ORIGINAL_SHA256,
                         'window_start': hex(analyze.TARGET), 'window_bytes': analyze.WINDOW_BYTES},
            'original window identity')
    require(digest(ROOT / original['path']) == original['sha256'], 'captured original bytes')
    source = result['source_file']
    require(source['path'] == 'programs/pump/src/multi_hop_curve_swap.rs', 'source path')
    require(source['sha256'] == '774c0e0f0b45e5fc924f5695a7c3106a11d93563f04c6d2ba8078097ea1161f9',
            'recorded source identity')
    require(result['analysis_inputs'] == implementation_hashes(), 'measurement implementation identity')
    measurements = result['verified_measurements']
    require(isinstance(measurements, list) and len(measurements) == 1, 'measurement membership')
    row = measurements[0]
    require(row['id'] == 'macos-identity-20a1ae9c', 'measurement identity')
    require(row['source_commit'] == '20a1ae9c0f243669f8ffb4633ee017b50f55958e', 'source commit')
    for key in ('source_manifest_sha256', 'source_manifest_file_sha256', 'candidate_stripped_sha256'):
        require(isinstance(row[key], str) and re.fullmatch('[0-9a-f]{64}', row[key]), key)
    measurement = row['measurement']
    require(measurement['original_sha256'] == original['sha256'], 'measurement original')
    require(measurement['original_start'] == original['window_start'], 'measurement start')
    require(type(measurement['bytes']) is int and measurement['bytes'] == analyze.WINDOW_BYTES, 'measurement size')
    require(analyze.SYMBOL.fullmatch(measurement['symbol']), 'candidate symbol')
    require(re.fullmatch('0x[0-9a-f]+', measurement['candidate_start']), 'candidate address')
    require(int(measurement['candidate_start'], 16) % 8 == 0, 'candidate alignment')
    require(re.fullmatch('[0-9a-f]{64}', measurement['candidate_unstripped_sha256']), 'candidate digest')
    positions = measurement['positions']
    require(isinstance(positions, list) and positions, 'positions')
    require(all(isinstance(p, str) and re.fullmatch('0x[0-9a-f]+', p) for p in positions), 'position spelling')
    values = [int(p, 16) for p in positions]
    require(values == sorted(set(values)), 'unique sorted positions')
    require(all(0 <= v < analyze.WINDOW_BYTES for v in values), 'position range')
    require(type(measurement['normalized_diff_bytes']) is int
            and measurement['normalized_diff_bytes'] == len(values), 'position count')
    require(type(measurement['raw_diff_bytes']) is int
            and 0 <= measurement['raw_diff_bytes'] <= analyze.WINDOW_BYTES, 'raw count')
    expected = [{'first_offset': hex(group[0]), 'last_offset': hex(group[-1]),
                 'diff_bytes': len(group)} for group in analyze.clusters(values)]
    require(measurement['clusters'] == expected, 'cluster membership')
    require(result['author_reported']['status'].startswith('unverified;'), 'author-reported boundary')
    require('not been independently verified' in result['author_reported']['interpretation_status'],
            'interpretation boundary')
    return row


def verify_packet(folder=HERE):
    verify_checksums(folder)
    result = json.loads((folder / 'RESULT.json').read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    return result, validate_result(result)


def synthetic_candidate(raw, symbol, address=0x1000):
    names = b'\0.shstrtab\0.text\0.strtab\0.symtab\0'
    strings = b'\0' + symbol.encode() + b'\0'
    text_offset = 512
    string_offset = text_offset + len(raw)
    symbol_offset = (string_offset + len(strings) + 7) & ~7
    blob = bytearray(symbol_offset + 48)
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', blob, 16, 3, 247, 1)
    struct.pack_into('<H', blob, 52, 64)
    struct.pack_into('<Q', blob, 40, 64)
    struct.pack_into('<HHH', blob, 58, 64, 5, 1)
    blob[384:384 + len(names)] = names
    blob[text_offset:text_offset + len(raw)] = raw
    blob[string_offset:string_offset + len(strings)] = strings
    headers = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
               (1, 3, 0, 0, 384, len(names), 0, 0, 1, 0),
               (11, 1, 6, address, text_offset, len(raw), 0, 0, 8, 0),
               (17, 3, 0, 0, string_offset, len(strings), 0, 0, 1, 0),
               (25, 2, 0, 0, symbol_offset, 48, 3, 0, 8, 24)]
    for index, values in enumerate(headers):
        struct.pack_into('<IIQQQQIIQQ', blob, 64 + 64 * index, *values)
    struct.pack_into('<IBBHQQ', blob, symbol_offset + 24, 1, 18, 0, 2, address, len(raw))
    return blob


class IntegrityControls(unittest.TestCase):
    def test_metadata_mutations_are_rejected(self):
        original = json.loads((HERE / 'RESULT.json').read_text(encoding='utf-8'))
        edits = [lambda r: r['original'].update(window_bytes=8),
                 lambda r: r['source_file'].update(sha256='0' * 64),
                 lambda r: r['analysis_inputs'].update({'score.normalize': '0' * 64}),
                 lambda r: r['verified_measurements'][0]['measurement'].update(bytes=True),
                 lambda r: r['verified_measurements'][0]['measurement']['positions'].append('0x29f9'),
                 lambda r: r['verified_measurements'][0]['measurement'].update(raw_diff_bytes=-1),
                 lambda r: r['verified_measurements'][0]['measurement']['clusters'][0].update(diff_bytes=0),
                 lambda r: r['author_reported'].update(status='verified')]
        for edit in edits:
            with self.subTest(edit=edit):
                changed = copy.deepcopy(original)
                edit(changed)
                with self.assertRaises(ValueError):
                    validate_result(changed)

    def test_checksum_mutation_and_missing_member_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name in FILES | {'SHA256SUMS'}:
                shutil.copyfile(HERE / name, folder / name)
            verify_checksums(folder)
            readme = folder / 'README.md'
            readme.write_bytes(readme.read_bytes() + b'changed')
            with self.assertRaises(ValueError):
                verify_checksums(folder)
            shutil.copyfile(HERE / 'README.md', readme)
            sums = folder / 'SHA256SUMS'
            sums.write_text('\n'.join(sums.read_text().splitlines()[1:]) + '\n')
            with self.assertRaises(ValueError):
                verify_checksums(folder)

    def test_candidate_symbols_sizes_and_relocated_reads(self):
        raw, _ = analyze.original_window()
        symbol = '_ZN14pump_recovered15multi_hop_curve8swap_hop17h0000000000000000E'
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            candidate.write_bytes(synthetic_candidate(raw, 'unrelated'))
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                analyze.measure(candidate)
            candidate.write_bytes(synthetic_candidate(raw[:-8], symbol))
            with self.assertRaisesRegex(ValueError, 'size'):
                analyze.measure(candidate)
            candidate.write_bytes(synthetic_candidate(raw, symbol))
            measured = analyze.measure(candidate)
            self.assertEqual(measured['candidate_start'], '0x1000')
            self.assertEqual(measured['raw_diff_bytes'], 0)
            self.assertEqual(measured['bytes'], analyze.WINDOW_BYTES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--source-manifest', type=Path)
    args = parser.parse_args()
    try:
        packet, row = verify_packet()
        if args.candidate is not None:
            measured = analyze.measure(args.candidate)
            require(measured == row['measurement'], 'candidate does not reproduce recorded measurement')
        if args.source_manifest is not None:
            require(digest(args.source_manifest) == row['source_manifest_file_sha256'], 'source manifest file hash')
            source_manifest = json.loads(args.source_manifest.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
            require(source_manifest['sha256'] == row['source_manifest_sha256'], 'source manifest identity')
            files = [item for item in source_manifest['files'] if item['path'] == 'src/multi_hop_curve_swap.rs']
            require(len(files) == 1 and files[0]['sha256'] == packet['source_file']['sha256'],
                    'source manifest window source binding')
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(IntegrityControls))
    if not result.wasSuccessful():
        return 1
    current_source = ROOT / packet['source_file']['path']
    print(json.dumps({'packet_checks': 'OK', 'candidate_recomputed': args.candidate is not None,
                      'source_manifest_verified': args.source_manifest is not None,
                      'current_source_matches_record': current_source.is_file() and
                          digest(current_source) == packet['source_file']['sha256']}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
