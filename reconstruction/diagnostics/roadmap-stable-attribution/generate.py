#!/usr/bin/env python3
"""Generate stable nearest named-context diagnostics from the reviewed roadmap."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'scripts/reconstruction_roadmap.py'
REVIEWED = 'e7f51159a9345abe7e7434ecda88346023446b47fc56aab01d0a2d1867b9603f'


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
    root, output = Path(root).resolve(), Path(output).resolve()
    raw = (root / SOURCE).read_bytes()
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != REVIEWED:
        raise ValueError('unreviewed roadmap source')
    if output.exists():
        raise ValueError('output already exists; retain prior packets')
    sys.path.insert(0, str(root / 'scripts'))
    module = types.ModuleType('reviewed_roadmap')
    module.__file__ = str(root / SOURCE)
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    module.trace_handler_attribution = trace_handler_attribution
    module.generate_roadmap(output)
    bindings = {SOURCE: hashlib.sha256(raw).hexdigest(),
                'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (output / 'attribution-inputs.json').write_text(json.dumps(bindings, indent=2) + '\n', encoding='utf-8')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())
                if p.is_file() and p.name != 'manifest.json'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        generate(args.repo, args.output)
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
