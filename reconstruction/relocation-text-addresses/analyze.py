"""Source-bound relocation reporting with virtual-to-file text translation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = 'e074929f474a6b98153bb6fd12f7943fa45d80ba10750c9967e334feee0e59e1'
READER_SHA256 = '247700e9930d5e53daf93a50888ae1e5429f74ccb19155e7a205f72ee21d5883'


def reviewed(source=None, *, corrected=True):
    path = Path(source) if source is not None else ROOT / 'scripts/deep_section_analysis.py'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('archived section analyzer digest mismatch')
    reader_path = ROOT / 'scripts/window_elf_reader.py'
    reader_raw = reader_path.read_bytes()
    if hashlib.sha256(reader_raw).hexdigest() != READER_SHA256:
        raise ValueError('archived ELF reader digest mismatch')
    text = raw.decode('utf-8')
    if corrected:
        replacements = [
            ('        if elf.lo <= at < elf.hi:\n            target_section = ".text"\n', ''),
            (' and sec_name != ".text"', ''),
            ('        if target_section == ".text" and typ == 8 and elf.b[at] == 0x18:\n'
             '            imm_lo = struct.unpack_from("<I", elf.b, at + 4)[0]\n'
             '            imm_hi = struct.unpack_from("<I", elf.b, at + 12)[0]',
             '        text_section = elf.secs.get(".text")\n'
             '        position = text_section[4] + at - text_section[3] if text_section else -1\n'
             '        if (target_section == ".text" and typ == 8\n'
             '                and at + 16 <= text_section[3] + text_section[5]\n'
             '                and 0 <= position and position + 16 <= len(elf.b)\n'
             '                and elf.b[position] == 0x18):\n'
             '            imm_lo = struct.unpack_from("<I", elf.b, position + 4)[0]\n'
             '            imm_hi = struct.unpack_from("<I", elf.b, position + 12)[0]'),
        ]
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError('reviewed relocation substitution is not unique')
            text = text.replace(old, new)
    reader = types.ModuleType('window_elf_reader')
    reader.__file__ = str(reader_path)
    exec(compile(reader_raw, str(reader_path), 'exec'), reader.__dict__)
    module = types.ModuleType('reviewed_section_analysis')
    module.__file__ = str(ROOT / 'scripts/deep_section_analysis.py')
    previous = sys.modules.get('window_elf_reader')
    sys.modules['window_elf_reader'] = reader
    try:
        exec(compile(text, str(path), 'exec'), module.__dict__)
    finally:
        if previous is None:
            sys.modules.pop('window_elf_reader', None)
        else:
            sys.modules['window_elf_reader'] = previous
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--program', choices=['pump', 'pump_amm', 'pump_fees', 'mayhem'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    module = reviewed()
    elf = module.Elf(ROOT / 'evidence/original' / args.program / 'deployed.so')
    report = {
        'program': args.program,
        'binary_sha256': hashlib.sha256(elf.b).hexdigest(),
        'archived_analyzer_sha256': SOURCE_SHA256,
        'archived_reader_sha256': READER_SHA256,
        'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limit': 'Static relocation reporting only. The CLI retains the archived capture reader and is not a general ELF loader.',
        'relocations': module.analyze_relocations(elf),
    }
    with args.output.open('x', encoding='utf-8') as target:
        json.dump(report, target, indent=2)
        target.write('\n')


if __name__ == '__main__':
    main()
