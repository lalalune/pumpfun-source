#!/usr/bin/env python3
"""Portable read-only entrypoint for the retained callgraph census diagnostics."""
import argparse
import hashlib
import importlib.util
import os
import secrets
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
LANE = 'reconstruction/pump-main/lanes/callgraph-census'
REVIEWED = {'census.py': 'fbd917eb6e18485d78bc3c88b88d27f652f82a1305cf9a3b9756c234bcbdd87a', 'callid_audit.py': 'e99c63252b954babecb8559723872acea76e5d233680c871a9bef763f4b81709', 'dataref_audit.py': 'af21df696c2aa31f1ed2b45cff228b19fc0856507159e067e1641366906b5812', 'blocksim.py': 'f7ef66ad5db10e65ad2fcf0e2cc0ef7183c429bce427da6d6379e3efe7cfb202', 'hotness.py': 'f8a0d0f9f5f708d9fd83261a2cb223f4d5ecd03f1e22487b82e824a23847e2da'}
TOOLS = {'census': 'census.py', 'callid': 'callid_audit.py', 'dataref': 'dataref_audit.py',
         'blocksim': 'blocksim.py', 'hotness': 'hotness.py'}


def exclusive_report(path, text):
    # Complete each report privately before claiming its fresh destination.
    # A failed write must not leave a truncated file that blocks a retry.
    for _ in range(100):
        temporary = path.with_name(f'.census-{os.getpid()}-{secrets.token_hex(8)}')
        try:
            stream = temporary.open('x', encoding='utf-8', newline='\n')
        except FileExistsError:
            continue
        break
    else:
        raise FileExistsError('could not create a unique census report staging file')
    metadata = os.fstat(stream.fileno())
    identity = metadata.st_dev, metadata.st_ino
    try:
        with stream:
            written = stream.write(text)
        if os.name == 'nt':
            os.rename(temporary, path)  # Windows refuses an occupied destination.
            temporary = None
        else:
            os.link(temporary, path)  # Publish without replacing a late writer.
        return written
    finally:
        if temporary is not None:
            try:
                metadata = temporary.lstat()
            except FileNotFoundError:
                pass
            else:
                if (metadata.st_dev, metadata.st_ino) == identity:
                    temporary.unlink()


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
                  'dataref': (), 'hotness': ('json', 'md'), 'blocksim': ()}[args.tool]
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
