#!/usr/bin/env python3
"""Experiment-only build with arbitrary extra rustc flags on the root crate (diagnostics only).

  capture_llvm.py --src <crate> --work <dir> --out <dir> -- <rustc flags...>

e.g. block-frequency dump of one function (names kept so blocks are MIR bbN):
  -- -Z fewer-names=no -C llvm-args=-print-bfi -C llvm-args=-print-bfi-func-name=<mangled>
Proposed source never carries these flags. Output (stdout+stderr of cargo) goes to <out>/build.log.
"""
import argparse, json, subprocess, sys
from pathlib import Path

sys.path.insert(0, '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
import fastbuild  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True); ap.add_argument('extra', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    extra = [x for x in a.extra if x != '--']
    real = subprocess.run

    def run(cmd, *ra, **kw):
        if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
            cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
        return real(cmd, *ra, **kw)
    subprocess.run = run
    try:
        res = fastbuild.build(a.src, a.work, a.out, recipe='identity', quiet=True)
    finally:
        subprocess.run = real
    print(json.dumps({k: res.get(k) for k in ('ok', 'seconds', 'unstripped_sha256')}))


if __name__ == '__main__':
    main()
