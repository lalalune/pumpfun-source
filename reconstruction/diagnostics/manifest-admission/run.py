#!/usr/bin/env python3
"""Run the retained batch revalidator with bounded manifest admission."""
import argparse
import hashlib
from pathlib import Path
import sys
import types
from check import check_manifest

ROOT = Path(__file__).resolve().parents[3]
# Digest of the reviewed scripts/revalidate_all.py this entrypoint pins; refresh
# it whenever the frozen script set moves through a reviewed asset transition.
REVIEWED = '2d037c093e69a94c8a9f9c78a01a671506dd2c9f4fb50f603e752caf249c622a'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.repo.resolve(), args.output.absolute()
    source = root / 'scripts/revalidate_all.py'
    raw = source.read_bytes()
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != REVIEWED:
        parser.error('reviewed revalidator source changed')
    if output.exists() or output.is_symlink():
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
