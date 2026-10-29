"""Replace the archived small-constant token heuristic with real token-program loads.

`scripts/bytecode_signatures.py::detect_token_transfer_patterns` looks for
`lddw` immediates equal to 3, 7 or 12, then labels them `spl_token_instruction`.
Those values are instruction-data bytes, not instructions, and no captured
program stores a token discriminant in a code immediate. The detector reports
zero rows for all four originals.

The real constant is the 32-byte SPL Token or Token-2022 program address,
assembled by four consecutive `lddw` loads. This packet hash-checks the archived
helper, detects exactly those four-load constants in a window, and reports the
real before/after counts. It does not rewrite the archived script or claim a
transfer occurred.
"""
from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import struct
import sys
import types

P = Path(__file__).resolve().parent
REPO = next(
    parent for parent in P.parents
    if (parent / 'evidence/original/pump/deployed.so').is_file()
)
SOURCE = 'scripts/bytecode_signatures.py'
PROGRAMS = ('pump', 'pump_amm', 'pump_fees', 'mayhem')
TOKEN_PROGRAMS = {
    'Tokenkeg': bytes.fromhex(
        '06ddf6e1d765a193d9cbe146ceeb79ac1cb485ed5f5b37913a8cf5857eff00a9'
    ),
    'Tokenz': bytes.fromhex(
        '06ddf6e1ee758fde18425dbce46ccddab61afc4d83b90d27febdf928d8a18bfc'
    ),
}
LF_SHA256 = '8200e01f582be1a267d187e6340ac2d403c22cad26bfd65e2613e19ea8a55f76'
EXPECTED = {
    'pump': {'windows': 1035, 'rows': 4, 'Tokenkeg': 3, 'Tokenz': 1},
    'pump_amm': {'windows': 785, 'rows': 2, 'Tokenkeg': 1, 'Tokenz': 1},
    'pump_fees': {'windows': 585, 'rows': 3, 'Tokenkeg': 3, 'Tokenz': 0},
    'mayhem': {'windows': 441, 'rows': 20, 'Tokenkeg': 16, 'Tokenz': 4},
}
sha = lambda data: hashlib.sha256(data).hexdigest()


def _reviewed():
    path = REPO / SOURCE
    raw = path.read_bytes()
    lf = raw.replace(b'\r\n', b'\n')
    forms = {sha(raw), sha(lf), sha(lf.replace(b'\n', b'\r\n'))}
    if LF_SHA256 not in forms:
        raise ValueError('the reviewed bytecode-pattern source has changed')
    if str(REPO / 'scripts') not in sys.path:
        sys.path.insert(0, str(REPO / 'scripts'))
    module = types.ModuleType('reviewed_bytecode_signatures')
    module.__file__ = str(path)
    exec(compile(lf, str(path), 'exec'), module.__dict__)
    return module


def lddw_chunks(elf, start, end):
    chunks = []
    at = start
    while at + 8 <= end:
        if elf.b[at] == 0x18:
            if at + 16 > end:
                break
            low = struct.unpack_from('<I', elf.b, at + 4)[0]
            high = struct.unpack_from('<I', elf.b, at + 12)[0]
            chunks.append((at, (low | (high << 32)).to_bytes(8, 'little')))
            at += 16
        else:
            at += 8
    return chunks


def token_constants(elf, start, end):
    chunks = lddw_chunks(elf, start, end)
    rows = []
    for index in range(len(chunks) - 3):
        blob = b''.join(value for _, value in chunks[index:index + 4])
        for name, expected in TOKEN_PROGRAMS.items():
            if blob == expected:
                rows.append({
                    'offset': chunks[index][0] - start,
                    'token_program': name,
                    'program_id_hex': expected.hex(),
                    'lddw_slots': 4,
                })
    return rows


def check(root=REPO):
    root = Path(root).resolve()
    archived = _reviewed()
    from window_elf_reader import Elf
    programs = {}
    totals = Counter()
    for name in PROGRAMS:
        elf = Elf(root / 'evidence/original' / name / 'deployed.so')
        old_rows = new_rows = 0
        old_windows = new_windows = 0
        by_program = Counter()
        for index, start in enumerate(elf.entries):
            end = (elf.entries + [elf.hi])[index + 1]
            old = archived.detect_token_transfer_patterns(elf, start, end)
            new = token_constants(elf, start, end)
            old_rows += len(old)
            new_rows += len(new)
            old_windows += bool(old)
            new_windows += bool(new)
            for row in new:
                by_program[row['token_program']] += 1
            assert all(row['token_program'] not in TOKEN_PROGRAMS or
                       row['program_id_hex'] == TOKEN_PROGRAMS[row['token_program']].hex()
                       for row in new)
        expected = EXPECTED[name]
        assert len(elf.entries) == expected['windows'], (name, len(elf.entries))
        assert old_rows == 0, (name, old_rows)
        assert new_rows == expected['rows'], (name, new_rows)
        assert by_program['Tokenkeg'] == expected['Tokenkeg'], (name, by_program)
        assert by_program['Tokenz'] == expected['Tokenz'], (name, by_program)
        # Independent oracle: scan the complete lddw sequence again.
        oracle = token_constants(elf, elf.lo, elf.hi)
        assert len(oracle) == new_rows
        programs[name] = {
            'windows': len(elf.entries),
            'old_rows': old_rows,
            'new_rows': new_rows,
            'old_windows': old_windows,
            'new_windows': new_windows,
            'Tokenkeg': by_program['Tokenkeg'],
            'Tokenz': by_program['Tokenz'],
            'first_rows': [
                row for row in oracle[:3]
            ],
        }
        totals['windows'] += len(elf.entries)
        totals['old_rows'] += old_rows
        totals['new_rows'] += new_rows
        totals['old_windows'] += old_windows
        totals['new_windows'] += new_windows
        totals['Tokenkeg'] += by_program['Tokenkeg']
        totals['Tokenz'] += by_program['Tokenz']
    assert totals['old_rows'] == 0
    assert totals['new_rows'] == 29
    assert totals['new_windows'] == 19
    assert totals['Tokenkeg'] == 23 and totals['Tokenz'] == 6
    return {
        'script': SOURCE,
        'script_sha256': sha((root / SOURCE).read_bytes()),
        'method': 'four consecutive lddw chunks assembled into a 32-byte token program id',
        'old_scope': 'archived lddw immediates 3/7/12 labelled spl_token_instruction',
        'totals': dict(totals),
        'programs': programs,
    }


def seal(packet=P):
    packet = Path(packet)
    report = check(REPO)
    (packet / 'observations.json.gz').write_bytes(
        gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
    )
    (packet / 'coverage-delta.json').write_text(
        json.dumps({
            'kind': 'tooling',
            'scope': 'Token-program constant detection; no transfer or payload-byte claim.',
            'totals': report['totals'],
        }, indent=2) + '\n'
    )
    inventory = {
        str(path.relative_to(packet)): sha(path.read_bytes())
        for path in sorted(packet.rglob('*'))
        if path.is_file() and path.name != 'manifest.json'
        and '__pycache__' not in path.parts and path.suffix != '.pyc'
    }
    (packet / 'manifest.json').write_text(json.dumps(inventory, indent=2) + '\n')
    return report['totals']


if __name__ == '__main__':
    print(json.dumps(seal(), indent=2))
