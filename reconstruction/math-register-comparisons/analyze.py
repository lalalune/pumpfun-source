"""Source-bound successor for unsigned register comparison math candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA256 = 'e074929f474a6b98153bb6fd12f7943fa45d80ba10750c9967e334feee0e59e1'
READER_SHA256 = '247700e9930d5e53daf93a50888ae1e5429f74ccb19155e7a205f72ee21d5883'
OLD = 'opcode in (0x25, 0x35, 0xa5, 0xb5) and prev_op in ("add", "sub", "mul")'
NEW = 'opcode in (0x25, 0x2d, 0x35, 0x3d, 0xa5, 0xad, 0xb5, 0xbd) and prev_op in ("add", "sub", "mul")'


def load_analysis(source=None, *, corrected=True):
    path = Path(source) if source is not None else ROOT / 'scripts/deep_section_analysis.py'
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('archived section analyzer source digest mismatch')
    text = raw.decode('utf-8')
    if text.count(OLD) != 1:
        raise ValueError('comparison predicate is not unique')
    if corrected:
        text = text.replace(OLD, NEW)
    module = types.ModuleType('reviewed_section_analysis')
    module.__file__ = str(ROOT / 'scripts/deep_section_analysis.py')
    # The archived helper imports this reader. Check it before any execution.
    reader_path = ROOT / 'scripts/window_elf_reader.py'
    reader_raw = reader_path.read_bytes()
    if hashlib.sha256(reader_raw).hexdigest() != READER_SHA256:
        raise ValueError('archived ELF reader source digest mismatch')
    reader = types.ModuleType('window_elf_reader')
    reader.__file__ = str(reader_path)
    exec(compile(reader_raw, str(reader_path), 'exec'), reader.__dict__)
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
    parser.add_argument('--archived', action='store_true', help='run the unchanged predicate for comparison')
    args = parser.parse_args()
    module = load_analysis(corrected=not args.archived)
    binary = ROOT / 'evidence/original' / args.program / 'deployed.so'
    elf = module.Elf(binary)
    result = module.analyze_math_patterns(elf)
    report = {
        'program': args.program,
        'binary_sha256': hashlib.sha256(elf.b).hexdigest(),
        'analyzer_sha256': SOURCE_SHA256,
        'reader_sha256': READER_SHA256,
        'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'register_comparisons_enabled': not args.archived,
        'limit': 'Static pattern candidates only; no proof of overflow handling, runtime behavior or source equivalence.',
        'analysis': result,
    }
    # Exclusive creation preserves every previous report.
    with args.output.open('x', encoding='utf-8') as target:
        json.dump(report, target, indent=2)
        target.write('\n')


if __name__ == '__main__':
    main()
