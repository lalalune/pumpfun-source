#!/usr/bin/env python3
"""Portable read-only entrypoint for the retained callgraph census diagnostics."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import runpy
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
LANE = 'reconstruction/pump-main/lanes/callgraph-census'
REVIEWED = {'census.py': '9eb94926c1228c867857b0577adf9ae8cdd4881f76ca46c40950f4ab8676e757', 'callid_audit.py': 'c14d451600347dfe4777116089c2f24e04c5d09548c499b0a20e9f9a428edfd5', 'dataref_audit.py': '43f9702bcb5dd0842e67e8839b7606d2fbc45a74d088394805bc0ec3aca0ca68', 'blocksim.py': '47d9e2d7915d99416b9d8275a848f327cf2c68403e85e17e2b546b6c4cb949b2', 'hotness.py': '9089fcda1e30c7d131ea0c1507b281c591f742145997a0afbf1c216f3a6d5b83'}
TOOLS = {'census': 'census.py', 'callid': 'callid_audit.py', 'dataref': 'dataref_audit.py',
         'blocksim': 'blocksim.py', 'hotness': 'hotness.py'}


def load_harness(name, root):
    path = root / 'reconstruction/harness' / f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=TOOLS)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    lane = ROOT / LANE
    for name, digest in REVIEWED.items():
        raw = (lane / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(raw).hexdigest() != digest:
            parser.error(f'reviewed lane source changed: {name}')
    for index, argument in enumerate(args.arguments):
        for flag in ['--json', '--md']:
            value = argument[len(flag) + 1:] if argument.startswith(flag + '=') else (
                args.arguments[index + 1] if argument == flag and index + 1 < len(args.arguments) else None)
            if value is not None and Path(value).exists():
                parser.error('output already exists; preserve prior diagnostics')
    with tempfile.TemporaryDirectory(prefix='pump-census-inputs-') as temporary:
        staged = Path(temporary).resolve()
        assert staged.parent == Path(tempfile.gettempdir()).resolve()
        assert staged.name.startswith('pump-census-inputs-')
        base = staged / 'base'
        base.mkdir()
        # Stage only authoritative original inputs. This also works when Git on
        # Windows checked original.so out as symlink text rather than an ELF.
        shutil.copyfile(ROOT / 'evidence/original/pump/deployed.so', base / 'original.so')
        shutil.copyfile(ROOT / 'reconstruction/base/functions.tsv', base / 'functions.tsv')
        sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
        sys.path.insert(0, str(lane))
        score = load_harness('score', ROOT)
        score.BASE = base
        # Load actual repository modules before the archived personal H path can
        # select unrelated modules. No scorer or decoder function is replaced.
        load_harness('win', ROOT)
        load_harness('coords', ROOT)
        script = lane / TOOLS[args.tool]
        sys.argv = [str(script), *args.arguments]
        runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    main()
