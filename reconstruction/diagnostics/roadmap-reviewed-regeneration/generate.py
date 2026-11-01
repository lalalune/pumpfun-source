#!/usr/bin/env python3
"""Guard archived roadmap regeneration with a fixed reviewed-source digest."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import types
import uuid

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = 'research/tooling-roadmap-call-classification-20261029/proof.py'
SOURCE = 'scripts/reconstruction_roadmap.py'
ARCHIVED = 'research/tooling-roadmap-call-classification-20261029/archived/reconstruction_roadmap.py'
# Values come from reviewed repository assets, never the current input bytes.
REVIEWED = {
    SOURCE: '529e187a98c05fc83cb17b80972594897d23a9eef75e30cb55b76341b05bc88a',
    ARCHIVE: '4acff7a33fff43773b730b4518a8beb8685abc683740945f27c9296ab4031800',
    ARCHIVED: 'e7f51159a9345abe7e7434ecda88346023446b47fc56aab01d0a2d1867b9603f',
}


def admitted_inputs(root, sources=None):
    bindings = {}
    for relative, expected in REVIEWED.items():
        raw = (root / relative).read_bytes() if sources is None else sources[relative]
        if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != expected:
            raise ValueError(f'unreviewed source: {relative}')
        bindings[relative] = hashlib.sha256(raw).hexdigest()
    return bindings


def generate(root, output):
    root, output = Path(root).resolve(), Path(output).absolute()
    sources = {relative: (root / relative).read_bytes() for relative in REVIEWED}
    bindings = admitted_inputs(root, sources)
    if output.exists() or output.is_symlink():
        raise ValueError('output already exists; retain prior results')
    proof = types.ModuleType('reviewed_call_proof')
    proof.__file__ = str(root / ARCHIVE)
    exec(compile(sources[ARCHIVE], proof.__file__, 'exec'), proof.__dict__)
    def load_archived(selected=root):
        sys.path.insert(0, str(Path(selected) / 'scripts'))
        module = types.ModuleType('reviewed_reconstruction_roadmap')
        module.__file__ = str(Path(selected) / SOURCE)
        exec(compile(sources[ARCHIVED], str(root / ARCHIVED), 'exec'), module.__dict__)
        return module
    proof._load_archived = load_archived
    for name in proof.PROGRAMS:
        path = f'evidence/original/{name}/deployed.so'
        bindings[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    report = proof.check(root)
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
        (stage / 'observations.json').write_text(json.dumps(report, indent=2) + '\n',
                                                       encoding='utf-8', newline='\n')
        (stage / 'inputs.json').write_text(json.dumps(bindings, indent=2) + '\n',
                                                   encoding='utf-8', newline='\n')
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.iterdir())}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                                     encoding='utf-8', newline='\n')
        for name, digest in bindings.items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
                raise ValueError('input changed during regeneration: ' + name)
        sys.path.insert(0, str(ROOT / 'scripts'))
        from deep_disassembly import rename_directory
        rename_directory(stage, output)
        stage = None
    except BaseException:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)
        raise
    return report['totals']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(generate(args.repo, args.output), indent=2))
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
