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
REVIEWED = {'census.py': '7b9924455f38a958aa16acdd9d23e5d27bf2eb4e352f6c65a9871a9d476c984a', 'callid_audit.py': 'a6a996056094f1f3f0a0dd827d4fca24c9d3e21becf222a249a1581752d3601c', 'dataref_audit.py': 'd850d110fe9c1a457b70f4d0adc8b7dd4ae96878a9fa8ea373fa68f0cc1b0a9e', 'blocksim.py': 'a45789eae91c9ac7ea30473a6960e72f45f3466bc2fe78cf06d1b2d0cabdf8a4', 'hotness.py': 'e6daa419e3103a6301c89fdfc666fbf31cd97f8a6403e1a5fdbba74cc0e762d1'}
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
