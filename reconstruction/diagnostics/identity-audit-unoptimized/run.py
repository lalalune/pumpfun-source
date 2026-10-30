#!/usr/bin/env python3
"""Keep the retained identity audit's hash/output assertions active."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
# Digests of the reviewed scripts/ sources this entrypoint pins; refresh them
# whenever the frozen script set moves through a reviewed asset transition.
REVIEWED = {'scripts/reconstruction_identity_audit.py': '6a5d3b27b82731110d0a7e585c5881d66656b2d4ba1c992f245f2a2030b06d45', 'scripts/analyze.py': 'd5c1350bcaa955257c80513a9e37bc91c5fe94b17691fe48506152eaddf3ffeb', 'scripts/compare.py': '374069ff669c8f911b6c1228d2ae4603b8aeb7bcdf4fa47eb6dec6c6e099f1e5'}
BOOTSTRAP = "import runpy,sys; from pathlib import Path; script=Path(sys.argv[1]); sys.path.insert(0,str(script.parent)); sys.argv=sys.argv[1:]; runpy.run_path(str(script),run_name='__main__')"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--index', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    sources = {}
    for name, digest in REVIEWED.items():
        raw = (root / name).read_bytes()
        if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != digest:
            parser.error(f'reviewed identity audit source changed: {name}')
        sources[name] = raw
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; preserve prior audits')
    # Run exactly the admitted bytes, including local imports. Public files may
    # change after admission; they must not supply unreviewed code to the child.
    with tempfile.TemporaryDirectory(prefix='identity-audit-reviewed-') as scratch:
        staged = Path(scratch)
        for name, raw in sources.items():
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        script = staged / 'scripts/reconstruction_identity_audit.py'
        # -I ignores an inherited PYTHONOPTIMIZE; omission of -O starts a normal
        # interpreter even when this entrypoint itself was invoked with -O/-OO.
        command = [sys.executable, '-I', '-B', '-X', 'utf8', '-c', BOOTSTRAP, str(script),
                   '--repo', str(root), '--index', args.index, '--output', str(args.output)]
        return subprocess.call(command)


if __name__ == '__main__':
    raise SystemExit(main())
