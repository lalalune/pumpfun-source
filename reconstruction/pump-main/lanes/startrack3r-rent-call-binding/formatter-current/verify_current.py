#!/usr/bin/env python3
"""Read-only replay on externally supplied, hash-pinned compiler outputs.

No build, binary patch, VM, network or runtime execution. Uses the pinned scorer
and the existing lane's complete-callee formatter binding. Works under python -O.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from verify_rent_edges import calls, formatter_span, require, sha


def read(path):
    return json.loads(path.read_bytes())


def store_immediates(raw):
    result = []
    offset = 0
    while offset < len(raw):
        size = 16 if raw[offset] == 0x18 else 8
        require(offset + size <= len(raw), 'Truncated instruction')
        if raw[offset] in (0x62, 0x6a, 0x72, 0x7a):
            result.append({'offset': offset, 'bytes': raw[offset:offset + size].hex()})
        offset += size
    return result


def check_callees(raw, start, windows, by_address):
    actual, syscalls = calls(raw, start)
    original, original_syscalls = calls(windows[0x80df8]['raw'], 0x80df8)
    require(len(actual) == len(original) == 17, 'V3 call count differs')
    require(syscalls == original_syscalls, 'V3 syscall bytes differ')
    result = []
    for old, new in zip(original, actual):
        target = windows[old['target']]
        shape = (target['bytes'], sha(target['norm']))
        require(new['offset'] == old['offset'], 'V3 call instruction moved')
        require(shape in by_address[new['target']], 'V3 actual callee differs')
        result.append({'offset': old['offset'], 'original_target': old['target'],
                       'candidate_target': new['target'], 'callee_bytes': shape[0],
                       'callee_normalized_sha256': shape[1]})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ['images', 'original', 'inventory', 'harness', 'work']:
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    summary = read(HERE / 'SUMMARY.json'); memberships = read(HERE / 'MEMBERSHIPS.json')
    pins = read(HERE / 'HARNESSES.json')
    # File hashes are observations, not attestations of historical compiler identity.
    require(sha(args.original.read_bytes()) == summary['original_sha256'], 'Original image differs')
    require(sha(args.inventory.read_bytes()) == summary['inventory_sha256'], 'Window inventory differs')
    for name, pin in pins['files'].items():
        require(sha((args.harness / name).read_bytes()) == pin['sha256'], 'Scorer file differs: ' + name)
    args.work.mkdir(parents=True, exist_ok=False)
    base = args.work / 'base'; base.mkdir()
    (base / 'original.so').write_bytes(args.original.read_bytes())
    (base / 'functions.tsv').write_bytes(args.inventory.read_bytes())
    sys.path.insert(0, str(args.harness))
    import score
    score.BASE = base
    windows = {w['start']: w for w in score.original_windows()}
    require(len(windows) == 1035, 'Incomplete original windows')
    original = args.original.read_bytes(); original_sections = score.sections(original)
    original_text = original_sections['.text']
    original_stores = len(store_immediates(original[original_text['offset']:original_text['offset'] + original_text['size']]))
    require(original_stores == 8535, 'Original text store count differs')
    images = {}; candidate_refs = None
    for name, expected in summary['images'].items():
        path = args.images / name / 'symbols.so'; raw = path.read_bytes()
        require(sha(raw) == expected['sha256'], 'Compiler image differs: ' + name)
        sections = score.sections(raw); functions = score.candidate_functions(path)
        physical = {}; by_address = defaultdict(set)
        for start, size, symbol in functions:
            body = score.body(raw, sections, start, size)
            shape = (size, sha(score.normalize(body, start, sections)))
            physical[(start, size)] = shape; by_address[start].add(shape)
        candidates = [f for f in functions if '5trade12v3_buy_costs17h' in f[2]]
        require(len(candidates) == 1, 'Ambiguous V3 symbol')
        start, size, symbol = candidates[0]
        body = score.body(raw, sections, start, size)
        norm = score.normalize(body, start, sections)
        measured, digest = score.score_with_hash(path)
        require(digest == sha(raw) and set(measured) == set(windows), 'Scored input differs')
        actual = {key: sorted(a for a, v in measured.items() if v[key]) for key in ['normalized', 'raw']}
        require(actual == memberships[name], 'Complete scorer membership differs: ' + name)
        text = sections['.text']; text_raw = raw[text['offset']:text['offset'] + text['size']]
        row = {'sha256': digest, 'bytes': len(raw), 'text_delta': text['size'] - original_sections['.text']['size'],
               'normalized': len(actual['normalized']), 'raw': len(actual['raw']),
               'v3_bytes': size, 'v3_normalized_sha256': sha(norm),
               'v3_normalized_equal': norm == windows[0x80df8]['norm'],
               'v3_raw_equal': body == windows[0x80df8]['raw'],
               'v3_store_immediates': store_immediates(body),
               'text_store_immediates': len(store_immediates(text_raw))}
        if name in summary['formatter_spans']:
            row['formatter'] = formatter_span(score, windows, raw, sections, physical, by_address)
            require(row['formatter']['delta'] == summary['formatter_spans'][name]['span_delta'], 'Formatter span differs')
        if name == '08-pr2272':
            require(row['v3_normalized_equal'] and not row['v3_raw_equal'], 'Expected normalized-only V3 match absent')
            candidate_refs = check_callees(body, start, windows, by_address)
            # A real wrong-callee operand remains normalized-identical but must fail binding.
            modified = bytearray(body); first = calls(body, start)[0][0]
            struct.pack_into('<i', modified, first['offset'] + 4, (start - (start + first['offset'] + 8)) // 8)
            require(score.normalize(modified, start, sections) == norm, 'Negative case changed normalized bytes')
            rejected = False
            try:
                check_callees(modified, start, windows, by_address)
            except ValueError:
                rejected = True
            require(rejected, 'Wrong-callee negative case was accepted')
        images[name] = row
    baseline = memberships['07-main-2b858']; candidate = memberships['08-pr2272']
    gains = sorted(set(candidate['normalized']) - set(baseline['normalized']))
    require(gains == [0x80df8] and set(baseline['normalized']) <= set(candidate['normalized']), 'Unexpected normalized gain/loss')
    require(candidate['raw'] == baseline['raw'], 'Raw membership changed')
    for version in ['143', '144']:
        for name in ['SBFInstrInfo.td', 'SBFTargetFeatures.td']:
            path = HERE / ('backend' + version) / name; blob = path.read_bytes()
            receipt = read(path.with_name(name + '.receipt.json'))
            require(hashlib.sha1(b'blob ' + str(len(blob)).encode() + b'\0' + blob).hexdigest() == receipt['git_blob'], 'Backend source Git blob differs')
    old = (HERE / 'backend143/SBFInstrInfo.td').read_text()
    new = (HERE / 'backend144/SBFInstrInfo.td').read_text()
    require('class STORE_imm' not in old and 'class STORE_imm_V1' in new, 'Store pattern evidence differs')
    require('let Predicates = [SBFHasStoreImm, SBFOldMemEncoding]' in new, 'Store feature predicate absent')
    require(images['06-sdk143-root-paths']['text_store_immediates'] == 0, 'Unexpected v1.43 immediate store')
    require(len(store_immediates(windows[0x80df8]['raw'])) == 24, 'Original V3 store count differs')
    report = {'result': 'PASS', 'images': images, 'v3_callees': candidate_refs,
              'original_text_store_immediates': original_stores,
              'normalized_gains': gains, 'normalized_losses': [], 'raw_gains': [], 'raw_losses': [],
              'wrong_callee_negative_test': 'rejected despite identical normalized body',
              'scope': 'Pinned output/byte observations only. No behavioral equivalence, historical provenance or raw-program identity claim.'}
    (args.work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
