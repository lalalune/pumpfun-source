#!/usr/bin/env python3
"""Generate stable nearest named-context diagnostics from the reviewed roadmap."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import types
import uuid

ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'scripts/reconstruction_roadmap.py'
REVIEWED = '529e187a98c05fc83cb17b80972594897d23a9eef75e30cb55b76341b05bc88a'
READER = 'scripts/window_elf_reader.py'
REVIEWED_READER = 'd3b57510531d7977110e73474cf89310b68bf6705d134ffb3bc759e18d30bedd'


def trace_handler_attribution(elf, entries, forward, reverse):
    named = {f['start']: f['name'] for f in elf.funcs if f['name']}

    def nearest(start, graph):
        distances, visited, queue = {}, set(), [start]
        for depth in range(1, 11):
            next_queue = []
            for address in queue:
                if address in visited:
                    continue
                visited.add(address)
                for target in graph.get(address, ()):
                    if target in named:
                        distances.setdefault(named[target], depth)
                    else:
                        next_queue.append(target)
            queue = next_queue
            if not queue:
                break
        return sorted(distances.items(), key=lambda item: (item[1], item[0]))

    result = {}
    for start in entries:
        if start in named:
            continue
        callers, callees = nearest(start, reverse), nearest(start, forward)
        if callers or callees:
            result[start] = {'likely_callers': callers, 'likely_callees': callees}
    return result


def generate(root, output):
    root, output = Path(root).resolve(), Path(output).absolute()
    raw = (root / SOURCE).read_bytes()
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != REVIEWED:
        raise ValueError('unreviewed roadmap source')
    reader_raw = (root / READER).read_bytes()
    if hashlib.sha256(reader_raw.replace(b'\r\n', b'\n')).hexdigest() != REVIEWED_READER:
        raise ValueError('unreviewed roadmap ELF reader')
    if output.exists() or output.is_symlink():
        raise ValueError('output already exists; retain prior packets')
    reader = types.ModuleType('reviewed_attribution_reader')
    reader.__file__ = str(root / READER)
    exec(compile(reader_raw, reader.__file__, 'exec'), reader.__dict__)
    module = types.ModuleType('reviewed_roadmap')
    module.__file__ = str(root / SOURCE)
    previous_reader = sys.modules.get('window_elf_reader')
    sys.modules['window_elf_reader'] = reader
    try:
        exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    finally:
        if previous_reader is None:
            sys.modules.pop('window_elf_reader', None)
        else:
            sys.modules['window_elf_reader'] = previous_reader
    module.trace_handler_attribution = trace_handler_attribution
    bindings = {SOURCE: hashlib.sha256(raw).hexdigest(),
                READER: hashlib.sha256(reader_raw).hexdigest(),
                'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for info in module.PROGRAMS.values():
        path = info['deployed']
        bindings[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    # Stage beside the destination and publish by rename, so a write failure
    # never leaves a partial packet at the destination: the destination check
    # above would otherwise block a retry at the same path, and the partial
    # directory would masquerade as a result although it has no manifest.
    # The stage is an ordinary mkdir, so it keeps the caller's umask.
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = None
    for _ in range(8):
        candidate = output.parent / ('.' + output.name + '.staging-' + uuid.uuid4().hex)
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        stage = candidate
        break
    if stage is None:
        raise FileExistsError('could not allocate a staging directory')
    try:
        module.generate_roadmap(stage)
        (stage / 'attribution-inputs.json').write_text(json.dumps(bindings, indent=2) + '\n',
                                                             encoding='utf-8', newline='\n')
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.iterdir())
                    if p.is_file() and p.name != 'manifest.json'}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                             encoding='utf-8', newline='\n')
        for name, digest in bindings.items():
            path = Path(__file__) if name == 'adapter_sha256' else root / name
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('input changed during attribution: ' + name)
        sys.path.insert(0, str(ROOT / 'scripts'))
        from deep_disassembly import rename_directory
        rename_directory(stage, output)
        stage = None
    except BaseException:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        generate(args.repo, args.output)
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
