"""Keep the twenty-field display cap out of the existing size heuristic."""
import argparse
import hashlib
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'scripts/deep_section_analysis.py'
SOURCE_SHA256 = {'a35097bc16fdc9a9f051b00671c523136d7d3a17467de33806f95cec707f54d4',
                 '805379ab5b529f77fd9207155f3bf0f19442a818749d3a55152f83007b861310'}


def corrected_module():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() not in SOURCE_SHA256:
        raise ValueError('The reviewed section-analysis source has changed')
    source = raw.decode().replace('\r\n', '\n')
    before = 'max(offsets[:20]) + 8 if offsets else 0'
    if source.count(before) != 1:
        raise ValueError('Reviewed size-estimate patch no longer applies')
    source = source.replace(before, 'max(offsets) + 8 if offsets else 0', 1)
    sys.path.insert(0, str(ROOT / 'scripts'))
    module = types.ModuleType('reviewed_full_offset_size_estimates')
    module.__file__ = str(SOURCE)
    exec(compile(source, str(SOURCE), 'exec'), module.__dict__)
    return module


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--program', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve prior evidence')
    sys.exit(corrected_module().main())
