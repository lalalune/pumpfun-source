#!/usr/bin/env python3
"""Recompute the retained Sell comparison; no compiler or VM is run here."""
import collections
import csv
import difflib
import gzip
import hashlib
import json
import re
import struct
import subprocess
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
import scorer as score  # Unmodified maintained scorer from upstream 60bdd8a7a.


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require_signatures(receipt):
    """Require every signature declared by the retained transaction message.

    verify_with_results() returns one result per signature, so an unsigned
    transaction yields an empty list and all() accepts it. Require at least
    one result before requiring all of them. The vector must also cover exactly
    the declared signers: a partial vector can contain only valid signatures.
    """
    import base64
    from solders.transaction import Transaction
    tx = Transaction.from_bytes(base64.b64decode(receipt['transaction_base64'], validate=True))
    results = tx.verify_with_results()
    required = tx.message.header.num_required_signatures
    require(required > 0 and len(tx.signatures) == len(results) == required and all(results),
            'invalid retained transaction signature')


def external_inputs(manifest):
    """Read external inputs from the replay revision, never the moving checkout."""
    revision = manifest['externalRevision']
    require(re.fullmatch(r'[0-9a-f]{40}', revision) is not None, 'external revision must be a full commit id')
    git = lambda *args: subprocess.run(['git', '-C', str(ROOT), *args], check=True, capture_output=True).stdout
    require(git('cat-file', '-t', revision).strip() == b'commit', 'external revision is not a commit')
    blobs = {}
    for path, expected in manifest['external'].items():
        blobs[path] = git('cat-file', 'blob', f'{revision}:{path}')
        require(digest(blobs[path]) == expected, f'external hash: {path}')
    return blobs


def read_json(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def functions(blob):
    """ELF64 STT_FUNC entries, cross-checked with llvm-objdump for both builds."""
    require(blob[:6] == b'\x7fELF\x02\x01', 'expected little-endian ELF64')
    offset = struct.unpack_from('<Q', blob, 40)[0]
    stride, count, strings = struct.unpack_from('<HHH', blob, 58)
    headers = [struct.unpack_from('<IIQQQQIIQQ', blob, offset + i * stride) for i in range(count)]
    names = headers[strings]
    pool = blob[names[4]:names[4] + names[5]]
    text_index = next(i for i, h in enumerate(headers) if pool[h[0]:pool.index(b'\0', h[0])] == b'.text')
    result = []
    for header in headers:
        if header[1] != 2:
            continue
        string_header = headers[header[6]]
        names = blob[string_header[4]:string_header[4] + string_header[5]]
        for pos in range(header[4], header[4] + header[5], header[9]):
            name, info, _, section, address, size = struct.unpack_from('<IBBHQQ', blob, pos)
            if info & 15 == 2 and section == text_index and size:
                result.append((address, size, names[name:names.index(b'\0', name)].decode()))
    return sorted(result)


def inventory(blob, rows):
    sections = score.sections(blob)
    return {address: {'size': size, 'name': name,
                     'raw': score.body(blob, sections, address, size),
                     'norm': score.normalize(score.body(blob, sections, address, size), address, sections)}
            for address, size, name in rows}


def census(original, candidate):
    by_normalized = collections.defaultdict(list)
    for function in candidate.values():
        by_normalized[function['norm']].append(function['raw'])
    return {str(start): {'normalized': function['norm'] in by_normalized,
                        'raw': function['raw'] in by_normalized[function['norm']]}
            for start, function in original.items()}


def tokens(raw):
    out = []
    i = 0
    while i < len(raw):
        width = 16 if raw[i] == 0x18 else 8
        out.append(raw[i:i + width])
        i += width
    return out


def edges(inv, start):
    raw = inv[start]['raw']
    out = []
    i = 0
    while i < len(raw):
        op, regs, _, imm = struct.unpack_from('<BBhi', raw, i)
        if op == 0x85:
            if regs >> 4 == 1 and imm != -1:
                target = start + i + 8 + imm * 8
                require(target in inv, f'unresolved actual call target {target:#x}')
                out.append(('internal', inv[target]['size'], digest(inv[target]['norm'])))
            else:
                out.append(('syscall', imm))
        i += 16 if op == 0x18 else 8
    return out


def main():
    manifest = read_json(HERE / 'manifest.json')
    for path, expected in manifest['packet'].items():
        require(digest((HERE / path).read_bytes()) == expected, f'packet hash: {path}')
    external = external_inputs(manifest)
    source_inputs = read_json(HERE / 'source-inputs.json')
    for label in ('control', 'candidate'):
        with tarfile.open(HERE / f'{label}-source.tar.gz', 'r:gz') as archive:
            members = {m.name: m for m in archive.getmembers() if m.isfile()}
            require(set(members) == set(source_inputs), 'source archive membership')
            for name, member in members.items():
                require(digest(archive.extractfile(member).read()) == source_inputs[name][label], f'source input: {name}')
    changed_inputs = [p for p, row in source_inputs.items() if row['control'] != row['candidate']]
    require(changed_inputs == ['programs/pump/src/trade_v3.rs'], 'unexpected source change')
    original_blob = external['evidence/original/pump/deployed.so']
    functions_tsv = external['reconstruction/base/functions.tsv'].decode('utf-8').splitlines()
    rows = [(int(r['original_start']), int(r['original_end']) - int(r['original_start']), r['candidate_names'])
            for r in csv.DictReader(functions_tsv, delimiter='\t')
            if r['program'] == 'pump' and r['variant'] == 'selected']
    original = inventory(original_blob, rows)
    inventories = {'original': original}
    blobs = {'original': original_blob}
    summaries = {}
    for label in ('control', 'candidate'):
        blob = gzip.decompress((HERE / f'{label}.so.gz').read_bytes())
        build = read_json(HERE / f'{label}-build.json')
        require(digest(blob) == build['unstripped_sha256'], 'build/image binding')
        require(build['ok'] and build['runtime_valid'] and not build['stack_warnings'], 'build failed or stack warning')
        require('exceeded max offset' not in gzip.decompress((HERE / f'{label}-build.log.gz').read_bytes()).decode(), 'stack overflow warning')
        inv = inventory(blob, functions(blob))
        inventories[label], blobs[label] = inv, blob
        current = census(original, inv)
        recorded = read_json(HERE / f'{label}-score.json.gz')['windows']
        # Recount over the recorded keys, not only over the windows this run
        # produced: a window the run dropped is not named by a comparison that
        # iterates the run's own result.
        require(set(current) == set(recorded) and all(current[k] == {f: recorded[k][f] for f in ('normalized', 'raw')} for k in recorded), 'official census disagreement')
        summaries[label] = {f: sum(v[f] for v in current.values()) for f in ('normalized', 'raw')}
        require(summaries[label] == {'normalized': 1020, 'raw': 188}, 'membership totals changed')
    for field in ('normalized', 'raw'):
        left, right = (census(original, inventories[k]) for k in ('control', 'candidate'))
        require({k for k, v in left.items() if v[field]} == {k for k, v in right.items() if v[field]}, 'membership loss or gain')
    symbol = '_ZN14pump_recovered5trade4sell17h3feba226d1168c0aE'
    by_name = {k: {v['name']: v for v in inventories[k].values()} for k in ('control', 'candidate')}
    require(by_name['control'].keys() == by_name['candidate'].keys(), 'function membership changed')
    changed = [n for n in by_name['control'] if by_name['control'][n]['norm'] != by_name['candidate'][n]['norm']]
    require(changed == [symbol], 'non-target normalized body changed')
    starts = {'original': 0x14a8a8}
    metrics = {}
    original_calls = edges(original, starts['original'])
    for label in ('control', 'candidate'):
        starts[label] = next(a for a, f in inventories[label].items() if f['name'] == symbol)
        target = inventories[label][starts[label]]
        require(edges(inventories[label], starts[label]) == original_calls, 'actual callee sequence differs')
        match = difflib.SequenceMatcher(None, tokens(original[0x14a8a8]['norm']), tokens(target['norm']), autojunk=False)
        metrics[label] = {'bytes': target['size'], 'ratio': match.ratio(),
                          'original_only': sum(i2-i1 for t,i1,i2,j1,j2 in match.get_opcodes() if t != 'equal'),
                          'candidate_only': sum(j2-j1 for t,i1,i2,j1,j2 in match.get_opcodes() if t != 'equal')}
    require(metrics['control']['original_only'] == 36 and metrics['control']['candidate_only'] == 37, 'control alignment')
    require(metrics['candidate']['original_only'] == 9 and metrics['candidate']['candidate_only'] == 10, 'candidate alignment')
    require(all(v['bytes'] == 6040 for v in metrics.values()), 'target size changed')
    for section in ('.rodata', '.data.rel.ro'):
        values = []
        for label in ('control', 'candidate'):
            h = score.sections(blobs[label])[section]
            values.append(blobs[label][h['offset']:h['offset'] + h['size']])
        require(values[0] == values[1], f'{section} changed')
    runtime = read_json(HERE / 'runtime.json.gz')
    if '--signatures' in sys.argv:
        for row in runtime['rows']:
            for receipt in row['receipts'].values():
                require_signatures(receipt)
    require(runtime['case_count'] == len(runtime['rows']) == 117, 'runtime case count')
    require(not runtime['differences'] and not runtime['regressions'], 'reported runtime difference')
    fields = ('error', 'accounts', 'inner_instructions', 'event_payloads', 'return_data')
    without_meter = lambda r: [line for line in r['logs'] if not re.search(r' consumed \d+ of \d+ compute units', line)]
    for row in runtime['rows']:
        receipts = row['receipts']
        require(all(r['signature_verified'] for r in receipts.values()), 'receipt signature flag')
        for label in ('control', 'candidate'):
            require(all(receipts[label][f] == receipts['original'][f] for f in fields), 'runtime surface difference')
            require(without_meter(receipts[label]) == without_meter(receipts['original']), 'runtime log difference')
    require(runtime['images']['original'] == digest(original_blob), 'runtime original hash')
    for label in ('control', 'candidate'):
        require(runtime['images'][label] == read_json(HERE / f'{label}-build.json')['candidate_sha256'], 'runtime compiled-image binding')
    print(json.dumps({'census': summaries, 'target': metrics, 'call_edges': len(original_calls),
                      'runtime_cases': len(runtime['rows']), 'recorded_executions': 3 * len(runtime['rows'])}, indent=2))


if __name__ == '__main__':
    main()
