#!/usr/bin/env python3
"""Run the retained batch revalidator with bounded manifest admission."""
import argparse
import hashlib
from pathlib import Path
import sys
import types
from check import check_manifest

ROOT = Path(__file__).resolve().parents[3]
# Fill from the reviewed base when packaging; the regression checks this binding.
REVIEWED = '1918e7b59bd232a3404336840e431367a9b69111d925b425d3e18948a4367d7f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.resolve()
    source = root / 'scripts/revalidate_all.py'
    raw = source.read_bytes()
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != REVIEWED:
        parser.error('reviewed revalidator source changed')
    if output.exists():
        parser.error('output already exists; preserve prior audits')
    module = types.ModuleType('reviewed_revalidator')
    module.__file__ = str(source)
    exec(compile(raw, str(source), 'exec'), module.__dict__)
    module.REPO = root
    module.check_manifest = check_manifest
    sys.argv = [str(source), '--output', str(output)]
    module.main()


if __name__ == '__main__':
    main()
