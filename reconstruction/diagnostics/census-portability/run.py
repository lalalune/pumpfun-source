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
REVIEWED = {'census.py': 'f854b2a1c6d4e0b98382edfe7c1562ed227720e3eeb5a2f088fcd89fec8f4eae', 'callid_audit.py': 'a5bd07c962b2d932835a10522c3d9b783b7a1089849458de7d7c070a60637219', 'dataref_audit.py': '49ad929379692acf03c29da322adc27da5e2cb3aec2ce5b737d6d3613ec60378', 'blocksim.py': 'd5e84c68a6b4c70c61e4cdb229fe22ba010adf8933edb2cf8c2f974112ace17a', 'hotness.py': '9089fcda1e30c7d131ea0c1507b281c591f742145997a0afbf1c216f3a6d5b83'}
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
