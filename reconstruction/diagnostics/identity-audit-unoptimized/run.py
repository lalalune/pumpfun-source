#!/usr/bin/env python3
"""Keep the retained identity audit's hash/output assertions active."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REVIEWED = {'scripts/reconstruction_identity_audit.py': '9f521f9850fa8a7627ed8d56e0a130ca3e12cb897105f5d844093be0d055ba3c', 'scripts/analyze.py': 'ee1270b0ab5a4df399b089ab38e4a0c4364fa975510cad5aff1deef10630a145', 'scripts/compare.py': '9e33a6c239927728b96bb1305bffad0e144a701e9ac7723928bb2f8d49f63e67'}
BOOTSTRAP = "import runpy,sys; from pathlib import Path; script=Path(sys.argv[1]); sys.path.insert(0,str(script.parent)); sys.argv=sys.argv[1:]; runpy.run_path(str(script),run_name='__main__')"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--index', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    for name, digest in REVIEWED.items():
        raw = (root / name).read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != digest:
            parser.error(f'reviewed identity audit source changed: {name}')
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; preserve prior audits')
    script = root / 'scripts/reconstruction_identity_audit.py'
    # -I ignores an inherited PYTHONOPTIMIZE; omission of -O starts a normal
    # interpreter even when this entrypoint itself was invoked with -O/-OO.
    command = [sys.executable, '-I', '-B', '-X', 'utf8', '-c', BOOTSTRAP, str(script),
               '--repo', str(root), '--index', args.index, '--output', str(args.output)]
    return subprocess.call(command)


if __name__ == '__main__':
    raise SystemExit(main())
