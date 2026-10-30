"""Bounded terminal-branch correction; archived bytecode script stays unchanged."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import types

P = Path(__file__).resolve().parent
REPO = P.parent.parent


def check_inputs():
    for name, expected in json.loads((P / 'inputs.json').read_text(encoding='utf-8')).items():
        if hashlib.sha256((REPO / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'bound input changed: {name}')


def reviewed():
    check_inputs()
    path = REPO / 'scripts/bytecode_signatures.py'
    module = types.ModuleType('reviewed_bytecode_signatures')
    module.__file__ = str(path)
    # The archived module imports the hash-checked window reader from scripts.
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


def detect_error_patterns(elf, start, end):
    """Detect Anchor error emission patterns.

    Typical pattern:
    1. Conditional branch (checking some condition)
    2. Load error code into register
    3. Call to error emission function
    """
    b = elf.b
    patterns = []
    offset = start
    # A branch can appear in the final slot and jump to an earlier move.
    # Bound the branch and its target independently instead of reserving a
    # three-instruction suffix that this detector never reads.
    while offset + 8 <= end:
        opcode = b[offset]
        # Look for: conditional branch + mov immediate + call/exit
        if opcode in (0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d,
                      0x55, 0x5d, 0x65, 0x6d, 0x75, 0x7d,
                      0xa5, 0xad, 0xb5, 0xbd):
            branch_off = struct.unpack_from("<h", b, offset + 2)[0]
            branch_target = offset + 8 + branch_off * 8
            # Check if branch leads to a mov + error pattern
            if start <= branch_target and branch_target + 8 <= end:
                next_at = branch_target
                if b[next_at] in (0xb7, 0xb4):  # mov imm
                    err_code = struct.unpack_from("<i", b, next_at + 4)[0]
                    patterns.append({
                        "offset": offset - start,
                        "branch_target_offset": branch_target - start,
                        "error_code": err_code,
                        "type": "conditional_error",
                    })
        if elf.b[offset] == 0x18:
            offset += 16
        else:
            offset += 8
    return patterns


def check():
    archived = reviewed()
    report = {'programs': {}}
    for name in archived.PROGRAMS:
        elf = archived.Elf(REPO / 'evidence/original' / name / 'deployed.so')
        bounds = elf.entries + [elf.hi]
        old_count = new_count = 0
        added = []
        for start, end in zip(bounds, bounds[1:]):
            old = archived.detect_error_patterns(elf, start, end)
            new = detect_error_patterns(elf, start, end)
            if any(row not in new for row in old):
                raise ValueError(f'archived candidate lost: {name} {start:#x}')
            old_count += len(old)
            new_count += len(new)
            for row in new:
                if row in old:
                    continue
                at = start + row['offset']
                target = start + row['branch_target_offset']
                if at < end - 24:
                    raise ValueError('unexpected non-terminal addition')
                added.append({'start': hex(start), 'end': hex(end),
                              'branch': hex(at), 'target': hex(target),
                              'branch_bytes': elf.b[at:at + 8].hex(),
                              'target_bytes': elf.b[target:target + 8].hex(),
                              'candidate': row})
        report['programs'][name] = {'windows': len(elf.entries),
                                   'before': old_count, 'after': new_count,
                                   'added': added}
    return report


if __name__ == '__main__':
    # Reuse the archived CLI with only this detector replaced in memory.
    archived = reviewed()
    archived.detect_error_patterns = detect_error_patterns
    archived.main()
