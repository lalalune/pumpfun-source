#!/usr/bin/env python3
"""Check the AMM workspace recipe inputs at the pinned source commit without compiling or running ELF."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
PACKET = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_recipe(root, relative, expected_sha256):
    # The path is fixed by this verifier; a packet edit cannot select other code.
    if relative != 'scripts/amm_sell/workspace_recipe.py' or PurePosixPath(relative).is_absolute():
        raise ValueError('Unexpected AMM recipe path')
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'Symlinked AMM recipe path: {path}')
    if not path.is_file():
        raise ValueError(f'Missing AMM recipe: {path}')
    source = path.read_bytes()
    if sha(source) != expected_sha256:
        raise ValueError('AMM workspace recipe changed from the pinned source')
    # Compile the same bytes just hashed; never consult an importlib .pyc cache.
    recipe = ModuleType('amm_workspace_recipe')
    recipe.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), recipe.__dict__)
    return recipe


INPUT_TREES = ('programs/pump-amm', 'crates/native-transfer-fee')


def tree_entries(revision, *paths):
    rows = {}
    raw = git('ls-tree', '-rz', revision, '--', *paths)
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1)
        mode, kind, object_id = header.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError(f'Unexpected tracked AMM input type: {name!r}')
        rows[name.decode()] = object_id
    return rows


def tree_blobs(revision):
    return tree_entries(revision, *INPUT_TREES)


def materialize(revision, recipe_path, destination):
    # Raw blob bytes: no checkout, attribute or end-of-line conversion applies.
    entries = tree_entries(revision, recipe_path, *INPUT_TREES)
    if recipe_path not in entries:
        raise ValueError('Pinned source commit does not track the AMM recipe')
    for name, object_id in entries.items():
        target = destination / PurePosixPath(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git('cat-file', 'blob', object_id))
        if git('hash-object', '--no-filters', '--', str(target)).decode().strip() != object_id:
            raise ValueError(f'Materialized AMM input differs from its Git blob: {name}')


def verify():
    manifest = json.loads((PACKET / 'recipe.json').read_text())
    commit = manifest['source_commit']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('source_commit must be an exact commit')
    if git('cat-file', '-t', commit).strip() != b'commit':
        raise ValueError('source_commit must identify a commit object')
    with tempfile.TemporaryDirectory(prefix='amm-recipe-') as temporary:
        source = Path(temporary) / 'source'
        materialize(commit, manifest['recipe_path'], source)
        recipe = load_recipe(source, manifest['recipe_path'], manifest['recipe_sha256'])

        inputs, workspace = recipe.expected_workspace(source)
        expected = manifest['source_inputs']
        if set(inputs) != set(expected):
            raise ValueError(f'AMM source inventory changed: missing={sorted(set(expected)-set(inputs))}, extra={sorted(set(inputs)-set(expected))}')
        tracked = tree_blobs(commit)
        selected_checkpoint = git('ls-tree', '-r', '--name-only', commit, '--', 'repro/pump_amm', 'repro/status.json')
        if selected_checkpoint:
            raise ValueError('Pinned source commit unexpectedly contains a selected AMM checkpoint')
        if set(tracked) != set(expected):
            raise ValueError(f'Tracked AMM tree differs from recipe inputs: missing={sorted(set(expected)-set(tracked))}, extra={sorted(set(tracked)-set(expected))}')
        for name, data in inputs.items():
            if sha(data) != expected[name]['sha256']:
                raise ValueError(f'Source-commit input differs from pinned AMM input: {name}')
            if tracked[name] != expected[name]['git_blob']:
                raise ValueError(f'Pinned commit blob differs from AMM input: {name}')

        if {name: sha(data) for name, data in workspace.items()} != manifest['staged_workspace_sha256']:
            raise ValueError('AMM workspace transformation differs from pinned recipe')
        staged = Path(temporary) / 'workspace'
        report = recipe.stage(source, staged)
        if report['standalone_inputs'] != len(expected) or report['workspace_inputs'] != len(workspace):
            raise ValueError('Unexpected workspace input counts')
        if report['input_sha256'] != {name: row['sha256'] for name, row in expected.items()}:
            raise ValueError('Staged workspace source receipt differs')
        if report['workspace_sha256'] != manifest['staged_workspace_sha256']:
            raise ValueError('Staged workspace receipt differs')
    return {
        'status': 'PASS', 'source_commit': manifest['source_commit'],
        'source_inputs': len(inputs), 'staged_workspace_inputs': len(workspace),
        'unchanged_rust_files': report['unchanged_rust_files'],
        'selected_checkpoint_tracked_at_source_commit': False,
        'compiled': False, 'original_elf_read': False, 'target_executed': False,
        'bytecode_identity_verified': False,
    }


if __name__ == '__main__':
    print(json.dumps(verify(), sort_keys=True, indent=2))
