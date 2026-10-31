#!/usr/bin/env python3
"""Portable read-only entrypoint for the retained callgraph census diagnostics."""
import argparse
import hashlib
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
LANE = 'reconstruction/pump-main/lanes/callgraph-census'
REVIEWED = {'census.py': '6c568cb9412341ee19b977ecc2ebdec03f51ed5ba6007f3a2e8efd4b01816835', 'callid_audit.py': 'a6a996056094f1f3f0a0dd827d4fca24c9d3e21becf222a249a1581752d3601c', 'dataref_audit.py': 'b8f184b78a5714a8deff63a6d2d823e297b843f23f6733365f9e0af5ab3e1982', 'blocksim.py': 'a45789eae91c9ac7ea30473a6960e72f45f3466bc2fe78cf06d1b2d0cabdf8a4', 'hotness.py': '9089fcda1e30c7d131ea0c1507b281c591f742145997a0afbf1c216f3a6d5b83'}
TOOLS = {'census': 'census.py', 'callid': 'callid_audit.py', 'dataref': 'dataref_audit.py',
         'blocksim': 'blocksim.py', 'hotness': 'hotness.py'}


def exclusive_report(path, text):
    # The early argument check is useful feedback, but another writer can
    # occupy that name while analysis runs. Refuse it at the actual open.
    with path.open('x') as stream:
        return stream.write(text)


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
    sources = {}
    for name, digest in REVIEWED.items():
        raw = (lane / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(raw).hexdigest() != digest:
            parser.error(f'reviewed lane source changed: {name}')
        sources[name] = raw
    for index, argument in enumerate(args.arguments):
        name, inline, attached = argument.partition('=')
        # The retained parsers also accept unambiguous prefixes such as --js.
        if len(name) > 2 and any(flag.startswith(name) for flag in ['--json', '--md']):
            value = attached if inline else (
                args.arguments[index + 1] if index + 1 < len(args.arguments) else None)
            if value is not None and (Path(value).exists() or Path(value).is_symlink()):
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
        text = sources[TOOLS[args.tool]].decode('utf-8')
        fields = {'census': ('json', 'md'), 'callid': ('json',),
                  'dataref': ('json',), 'hotness': ('json', 'md'), 'blocksim': ()}[args.tool]
        for field in ('json', 'md'):
            anchor = f'a.{field}.write_text('
            if text.count(anchor) != int(field in fields):
                parser.error('reviewed output substitution changed')
            text = text.replace(anchor, f'exclusive_report(a.{field}, ')
        try:
            exec(compile(text, str(script), 'exec'), {
                '__name__': '__main__', '__file__': str(script),
                'exclusive_report': exclusive_report,
            })
        except FileExistsError as error:
            parser.error('output appeared during diagnostics; preserve it: ' + str(error))


if __name__ == '__main__':
    main()
