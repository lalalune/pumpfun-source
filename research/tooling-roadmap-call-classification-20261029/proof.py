"""Correct the roadmap's call/syscall classification and report real counts.

`scripts/reconstruction_roadmap.py` decodes the source nibble with
`(byte >> 4) & 0xf` and compares it with `0x10`.  A nibble cannot equal 16, so
every captured call falls through to `call_other`: internal relative-call
targets are not counted and the per-window `syscalls` mapping is always empty.
The captured SBPF v0 corpus encodes both internal calls and relocated external
calls as `0x85 0x10`; relocation type 10 identifies the external placeholder.

This packet hash-checks the archived helper, applies only that comparison and
the matching call-count predicate in memory, and reports before/after counts
against the real captures.  It does not rewrite the archived script, its
historical reports or any original byte.
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
SCRIPTS = REPO / 'scripts'
SOURCE = 'scripts/reconstruction_roadmap.py'
PROGRAMS = ('pump', 'pump_amm', 'mayhem')
EXPECTED = {
    'pump': {'call_sites': 10861, 'internal_calls': 10591, 'external_calls': 270, 'windows': 1035},
    'pump_amm': {'call_sites': 7397, 'internal_calls': 7223, 'external_calls': 174, 'windows': 785},
    'mayhem': {'call_sites': 4902, 'internal_calls': 4768, 'external_calls': 134, 'windows': 441},
}
LF_SHA256 = 'e7f51159a9345abe7e7434ecda88346023446b47fc56aab01d0a2d1867b9603f'
CRLF_SHA256 = hashlib.sha256(
    (REPO / SOURCE).read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
).hexdigest()
REVIEWED = {LF_SHA256, CRLF_SHA256}
sha = lambda data: hashlib.sha256(data).hexdigest()


def _load_archived(root=REPO):
    path = Path(root) / SOURCE
    raw = path.read_bytes()
    digest = sha(raw)
    lf = raw.replace(b'\r\n', b'\n')
    if digest not in REVIEWED and sha(lf) not in REVIEWED:
        raise ValueError('the reviewed roadmap source has changed')
    if str(Path(root) / 'scripts') not in sys.path:
        sys.path.insert(0, str(Path(root) / 'scripts'))
    module = types.ModuleType('reviewed_reconstruction_roadmap')
    module.__file__ = str(path)
    exec(compile(lf, str(path), 'exec'), module.__dict__)
    return module


def corrected_classify(archived):
    """Return the archived classifier with the call rule corrected."""
    original = archived.classify_instruction

    def classify(data, offset, elf):
        if offset + 8 > len(data):
            return 'truncated'
        opcode = data[offset]
        if opcode != 0x85:
            return original(data, offset, elf)
        regs = data[offset + 1]
        src = (regs >> 4) & 0xF
        immediate = struct.unpack_from('<i', data, offset + 4)[0]
        relocation = elf.relocations.get(offset)
        if relocation is not None and relocation.get('type') == 10:
            return 'syscall_' + relocation.get('symbol', '?')
        if src == 1:
            return 'call_internal'
        if src == 0:
            return f'syscall_{immediate}'
        return 'call_other'

    return classify


def window_patterns(archived, elf, start, end, classify):
    """Archived window accounting with the corrected call predicate."""
    data = elf.b
    patterns = Counter()
    syscalls = Counter()
    calls = branches = exits = memory_ops = alu_ops = 0
    offset = start
    while offset < end:
        kind = classify(data, offset, elf)
        patterns[kind] += 1
        if kind.startswith(('call', 'syscall')):
            calls += 1
        if kind.startswith('syscall'):
            syscalls[kind] += 1
        if kind == 'branch':
            branches += 1
        elif kind == 'exit':
            exits += 1
        elif kind == 'memory':
            memory_ops += 1
        elif kind == 'alu':
            alu_ops += 1
        offset += 16 if data[offset] == 0x18 else 8
    instructions = sum(patterns.values())
    return {
        'instructions': instructions,
        'calls': calls,
        'branches': branches,
        'exits': exits,
        'memory_ops': memory_ops,
        'alu_ops': alu_ops,
        'syscalls': dict(syscalls.most_common()),
        'branch_density': round(branches / max(instructions, 1), 4),
        'call_density': round(calls / max(instructions, 1), 4),
        'complexity_score': branches + calls * 2,
        'classes': dict(patterns.most_common()),
    }


def count_classes(elf, start, end, classify):
    counts = Counter()
    offset = start
    while offset < end:
        counts[classify(elf.b, offset, elf)] += 1
        offset += 16 if elf.b[offset] == 0x18 else 8
    return counts


def _raw_call_counts(elf):
    internal = external = 0
    for at in range(elf.lo, elf.hi, 8):
        if elf.b[at] != 0x85:
            continue
        relocation = elf.relocations.get(at)
        if relocation is not None and relocation.get('type') == 10:
            external += 1
        else:
            internal += 1
    return internal, external


def check(root=REPO):
    root = Path(root).resolve()
    archived = _load_archived(root)
    classify = corrected_classify(archived)
    from window_elf_reader import Elf
    programs = {}
    totals = Counter()
    for name in PROGRAMS:
        elf = Elf(root / 'evidence/original' / name / 'deployed.so')
        before = Counter()
        after = Counter()
        before_classes = Counter()
        after_classes = Counter()
        windows = 0
        changed = 0
        for index, start in enumerate(elf.entries):
            end = (elf.entries + [elf.hi])[index + 1]
            old = archived.analyze_window_patterns(elf, start, end)
            new = window_patterns(archived, elf, start, end, classify)
            windows += 1
            for term, count in old['syscalls'].items():
                before[term] += count
            for term, count in new['syscalls'].items():
                after[term] += count
            before_classes.update(
                count_classes(elf, start, end, archived.classify_instruction)
            )
            after_classes.update(new['classes'])
            if old['syscalls'] != new['syscalls'] or old['calls'] != new['calls']:
                changed += 1
            assert old['instructions'] == new['instructions']
            assert old['branches'] == new['branches']
            assert old['exits'] == new['exits']
            assert old['memory_ops'] == new['memory_ops']
            assert old['alu_ops'] == new['alu_ops']
        internal, external = _raw_call_counts(elf)
        call_sites = internal + external
        assert call_sites == len(elf.calls) + external
        assert sum(after.values()) == external
        assert after_classes.get('call_internal', 0) == internal
        assert before_classes.get('call_internal', 0) == 0
        assert before_classes.get('call_other', 0) == call_sites
        assert sum(before.values()) == 0
        expected = EXPECTED[name]
        assert call_sites == expected['call_sites'], (name, call_sites)
        assert internal == expected['internal_calls'], (name, internal)
        assert external == expected['external_calls'], (name, external)
        assert windows == expected['windows'], (name, windows)
        programs[name] = {
            'windows': windows,
            'call_sites': call_sites,
            'internal_calls': internal,
            'external_calls': external,
            'windows_with_syscalls_before': 0,
            'windows_with_syscalls_after': sum(
                1 for index, start in enumerate(elf.entries)
                if window_patterns(archived, elf, start,
                                   (elf.entries + [elf.hi])[index + 1],
                                   classify)['syscalls']
            ),
            'changed_windows': changed,
            'syscall_terms_before': dict(before.most_common()),
            'syscall_terms_after': dict(after.most_common()),
            'call_internal_before': before_classes.get('call_internal', 0),
            'call_internal_after': after_classes.get('call_internal', 0),
            'call_other_before': before_classes.get('call_other', 0),
            'call_other_after': after_classes.get('call_other', 0),
        }
        totals['windows'] += windows
        totals['call_sites'] += call_sites
        totals['internal_calls'] += internal
        totals['external_calls'] += external
        totals['windows_with_syscalls_after'] += programs[name]['windows_with_syscalls_after']
        totals['changed_windows'] += changed
    assert totals['external_calls'] == 578
    return {
        'script': SOURCE,
        'script_sha256': sha((root / SOURCE).read_bytes()),
        'method': 'source-nibble comparison corrected; relocation type 10 separates external calls',
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
            'scope': 'Call/syscall classification correction; no payload-byte coverage claim.',
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
