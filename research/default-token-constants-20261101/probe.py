#!/usr/bin/env python3
"""Check the complete signature CLI against retained token-program constant loads."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace

PROGRAMS = ('pump', 'pump_amm', 'mayhem')
SOURCES = ('bytecode_signatures.py', 'window_elf_reader.py', 'deep_disassembly.py')
ACCEPTED = 'research/tooling-token-program-constant-detector-20261029/proof.py'
PROGRAM_IDS = {
    'Tokenkeg': '06ddf6e1d765a193d9cbe146ceeb79ac1cb485ed5f5b37913a8cf5857eff00a9',
    'Tokenz': '06ddf6e1ee758fde18425dbce46ccddab61afc4d83b90d27febdf928d8a18bfc',
}
EXPECTED = {'pump': 4, 'pump_amm': 2, 'mayhem': 20}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan(blob, start, end, relocations):
    """Decode four-load sequences directly, independently of the producer."""
    chunks = []
    position = start
    while position < end:
        width = 16 if blob[position] == 0x18 else 8
        require(position + width <= end, 'window ends inside an instruction')
        if width == 16:
            low = struct.unpack_from('<I', blob, position + 4)[0]
            high = struct.unpack_from('<I', blob, position + 12)[0]
            chunks.append((position, (low | (high << 32)).to_bytes(8, 'little')))
        position += width
    rows, witnesses = [], []
    for index in range(len(chunks) - 3):
        group = chunks[index:index + 4]
        if any(at in relocations for at, _ in group):
            continue
        value = b''.join(chunk for _, chunk in group).hex()
        for name, expected in PROGRAM_IDS.items():
            if value != expected:
                continue
            row = {'offset': group[0][0] - start, 'type': 'token_program_constant',
                   'token_program': name, 'program_id_hex': expected, 'lddw_slots': 4}
            rows.append(row)
            witnesses.append({'window': hex(start), 'program': name,
                              'load_offsets': [hex(at) for at, _ in group],
                              'raw_loads': [blob[at:at + 16].hex() for at, _ in group]})
    return rows, witnesses


def collect(repo, *, revision=None, expected='fixed'):
    repo = Path(repo).resolve()
    sources = {name: (subprocess.check_output(
        ['git', '-C', str(repo), 'show', f'{revision}:scripts/{name}'])
        if revision else (repo / 'scripts' / name).read_bytes()) for name in SOURCES}
    inputs = {name: (repo / 'evidence/original' / name / 'deployed.so').read_bytes()
              for name in PROGRAMS}
    accepted_bytes = (repo / ACCEPTED).read_bytes()
    result = {'expectation': expected,
              'source_sha256': {name: sha(data) for name, data in sources.items()},
              'input_sha256': {name: sha(data) for name, data in inputs.items()},
              'accepted_detector_sha256': sha(accepted_bytes), 'programs': {}}
    with tempfile.TemporaryDirectory(prefix='default-token-constants-') as temporary:
        root = Path(temporary)
        (root / 'scripts').mkdir()
        for name, data in sources.items():
            (root / 'scripts' / name).write_bytes(data)
        for name, data in inputs.items():
            path = root / 'evidence/original' / name / 'deployed.so'
            path.parent.mkdir(parents=True)
            path.write_bytes(data)
        accepted_path = root / ACCEPTED
        accepted_path.parent.mkdir(parents=True)
        accepted_path.write_bytes(accepted_bytes)
        accepted = load('accepted_token_constants', accepted_path)
        reader = load('token_probe_reader', root / 'scripts/window_elf_reader.py')
        output = root / 'packet'
        run = subprocess.run([sys.executable, '-B', str(root / 'scripts/bytecode_signatures.py'),
                              '--output', str(output)], capture_output=True, text=True, cwd=root, timeout=60)
        require(run.returncode == 0, run.stdout + run.stderr)
        verifier = subprocess.run([sys.executable, '-B', str(output / 'verify.py')],
                                  capture_output=True, text=True, cwd=root, timeout=30)
        require(verifier.returncode == 0, verifier.stdout + verifier.stderr)
        summary = json.loads((output / 'summary.json').read_bytes())
        for name, blob in inputs.items():
            elf = reader.Elf(root / 'evidence/original' / name / 'deployed.so')
            patterns = json.loads((output / f'{name}-patterns.json').read_bytes())
            signatures = json.loads((output / f'{name}-signatures.json').read_bytes())
            require(len(patterns) == len(signatures) == len(elf.entries), 'window counts differ')
            rows_total = reported_total = windows_total = 0
            witnesses = []
            for pattern, signature in zip(patterns, signatures):
                require(pattern['address'] == signature['address'], 'window identity differs')
                start = int(pattern['address'], 16)
                end = start + pattern['size']
                rows, sites = scan(blob, start, end, elf.relocations)
                historical = accepted.token_constants(SimpleNamespace(b=blob), start, end)
                require([{key: value for key, value in row.items() if key != 'type'}
                         for row in rows] == historical, 'accepted detector disagrees')
                wanted = rows if expected == 'fixed' else []
                require(pattern['tokens'] == wanted, 'reported token constants differ from retained bytes')
                require(signature['token_patterns'] == len(wanted), 'signature token count differs')
                rows_total += len(rows)
                reported_total += len(wanted)
                windows_total += bool(wanted)
                witnesses.extend(sites)
            require(rows_total == EXPECTED[name], 'retained constant count changed')
            require(summary['programs'][name]['windows_with_tokens'] == windows_total,
                    'summary token count differs')
            result['programs'][name] = {'windows': len(patterns), 'exact_constants': rows_total,
                'reported_constants': reported_total, 'windows_with_tokens': windows_total,
                'witnesses': witnesses}
        result['packet_sha256'] = {path.name: sha(path.read_bytes()) for path in sorted(output.iterdir())}
        unrelated = {}
        for path in sorted(output.iterdir()):
            if path.name == 'manifest.json':
                continue  # Its hashes necessarily change with the token report fields.
            data = path.read_bytes()
            if path.suffix == '.json':
                value = json.loads(data)
                if path.name in {f'{name}-{kind}.json' for name in PROGRAMS
                                 for kind in ('patterns', 'signatures')}:
                    key = 'tokens' if path.name.endswith('-patterns.json') else 'token_patterns'
                    for row in value:
                        del row[key]
                elif path.name == 'summary.json':
                    for row in value['programs'].values():
                        del row['windows_with_tokens']
                data = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
            elif path.name == 'README.md':
                lines = []
                for line in data.decode().splitlines():
                    if line == 'Token constants alone do not prove a transfer or CPI.':
                        continue
                    line = line.replace('token transfer,', 'TOKEN_DESCRIPTION,').replace(
                        'token-program constants,', 'TOKEN_DESCRIPTION,')
                    if any(line.startswith('| ' + name + ' |') for name in PROGRAMS):
                        cells = line.split('|')
                        cells[4] = ' TOKEN_COUNT '
                        line = '|'.join(cells)
                    lines.append(line)
                data = '\n'.join(lines).encode()
            unrelated[path.name] = sha(data)
        result['unrelated_report_sha256'] = unrelated
        result['generated_verifier_exit'] = verifier.returncode
        require(all((root / 'evidence/original' / name / 'deployed.so').read_bytes() == data
                    for name, data in inputs.items()), 'private capture bytes changed')
    require(all((repo / 'evidence/original' / name / 'deployed.so').read_bytes() == data
                for name, data in inputs.items()), 'retained capture bytes changed')
    require((repo / ACCEPTED).read_bytes() == accepted_bytes, 'accepted detector changed')
    result['all_input_bytes_preserved'] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.repo, revision=args.revision, expected=args.expect)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as target:
        json.dump(result, target, indent=2)
        target.write('\n')
    print(json.dumps({'expectation': args.expect, 'programs': {
        name: {key: value for key, value in row.items() if key != 'witnesses'}
        for name, row in result['programs'].items()}}))


if __name__ == '__main__':
    main()
