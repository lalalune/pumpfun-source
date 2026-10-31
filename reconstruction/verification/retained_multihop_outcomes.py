#!/usr/bin/env python3
"""Verify the archived sell-fee runtime cohort, not current-source acceptance.

Reuses all retained source/wire/prestate/loader/log joins, then checks exact
declared error outcomes. No compiler, producer, LiteSVM or network is executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PACKET = 'research/pump-multihop-sell-fees-20261029'
SOURCE_PINS = {
    'verify.py': '542afedae9f92b04de57e0585073d02c4993ac1626a77fe86a35c4b54815f51b',
    'correspondence.py': '453cbc7a59729df4d92e7bc64509516b055095592ccf6042b7fa75acfe0f6f9f',
    'runtime/input-map.json': 'd50f3eedcb2d456573378e3a4b32446bc8f841f00fa3d2b169332488689629ab',
    'runtime/inputs/upstream/runtime/inputs/base-fixture.json':
        '0f269b3e5766fc77fd493d41f68d31ad1b3fd865ac977709d6ba552a192e448f',
}
FIXTURE_PATH = 'research/pump-multi-hop-quote-admission/runtime/inputs/base-fixture.json'
IMAGE_PINS = {
    'parent': '47cb3e2aac8bd8b444a820d3ed4a11f37d58cd7da1ad571692f9b7d22a39887d',
    'candidate': 'a1a9223a33274b687d263a7ed263dbbd29429abe9532a61c3959b4d5b6e6bd2e',
}
FAMILIES = {
    'standard/regression-thirteen.json.gz':
        (None, None, 6063, 2006, 'InvalidAccountData', 2006, 2006, 2006, 6010, 6063, None, None, None),
    'standard/arithmetic-two.json.gz': (None, None),
    'upstream-gate/zeroquote-one.json.gz': (6041,),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_module(name, path, raw):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def retained_runtime(packet, repo):
    """Run the unchanged complete correspondence over an explicit archived view."""
    require(__debug__, 'Run without -O: the archived correspondence requires it')
    admitted = {}
    for name, expected in SOURCE_PINS.items():
        raw = (packet / name).read_bytes()
        require(sha(raw) == expected,
                'archived verifier/input source binding: ' + name)
        admitted[name] = raw
    gate = load_module('retained_multihop_gate', packet / 'verify.py', admitted['verify.py'])
    gate.manifest(packet)
    correspondence = load_module('retained_multihop_correspondence', packet / 'correspondence.py', admitted['correspondence.py'])
    images = {label: {'candidate': gate.read(packet / 'build' / label / 'candidate.so.gz')}
              for label in IMAGE_PINS}
    for label, expected in IMAGE_PINS.items():
        require(sha(images[label]['candidate']) == expected, 'archived candidate image binding: ' + label)

    # The original external fixture was removed from main. Use its exact pinned
    # retained copy in an owned filesystem view; never restore files in the repo.
    # The source-pinned input map contains only these captured evidence inputs.
    mapping = json.loads((packet / 'runtime/input-map.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='retained-multihop-view-') as temporary:
        view = Path(temporary)
        for name in sorted({row['path'] for row in mapping if row['kind'] == 'repo'}):
            require(name.startswith('evidence/') and gate.relative(name) == name,
                    'captured evidence input path')
            target = view / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / name, target)
        fixture = view / FIXTURE_PATH
        fixture.parent.mkdir(parents=True)
        shutil.copyfile(packet / 'runtime/inputs/upstream/runtime/inputs/base-fixture.json', fixture)
        return correspondence.verify(packet, view, images, gate.read, gate.doc)


def expected_error(value):
    if value is None:
        return None
    if isinstance(value, int):
        return f'TransactionErrorInstructionError((0, Tagged(InstructionErrorCustom({value}))))'
    return f'TransactionErrorInstructionError((0, Fieldless({value})))'


def verify(packet, repo):
    result = retained_runtime(packet, repo)
    import gzip
    for name, expected in FAMILIES.items():
        report = json.loads(gzip.decompress((packet / 'runtime' / name).read_bytes()))
        require(len(report['cases']) == len(expected), 'declared outcome case membership')
        for row, value in zip(report['cases'], expected):
            for role, run in row['runs'].items():
                require(run['error'] == expected_error(value),
                        f"exact declared outcome: {row['case']['name']} / {role}")
    return dict(verified=True, scope=__doc__, current_source_acceptance=False,
                compiler_executions=0, vm_executions=0, exact_declared_outcomes=True,
                archived_runtime=result)


def main():
    if not __debug__:
        raise SystemExit('Run without -O: the archived correspondence requires it')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=ROOT)
    parser.add_argument('--packet', type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    packet = (args.packet or repo / PACKET).resolve()
    print(json.dumps(verify(packet, repo), indent=2))


if __name__ == '__main__':
    main()
