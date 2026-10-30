#!/usr/bin/env python3
"""Check the tracked AMM workspace recipe inputs without compiling or running ELF."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PACKET = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree_blobs(revision):
    rows = {}
    raw = git('ls-tree', '-rz', revision, '--', 'programs/pump-amm', 'crates/native-transfer-fee')
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        header, name = entry.split(b'\t', 1)
        mode, kind, object_id = header.decode().split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError(f'Unexpected tracked AMM input type: {name!r}')
        rows[name.decode()] = object_id
    return rows


def verify():
    manifest = json.loads((PACKET / 'manifest.json').read_text())
    spec = importlib.util.spec_from_file_location('amm_workspace_recipe', ROOT / manifest['recipe_path'])
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    if sha((ROOT / manifest['recipe_path']).read_bytes()) != manifest['recipe_sha256']:
        raise ValueError('AMM workspace recipe changed from the pinned source')

    inputs, workspace = recipe.expected_workspace(ROOT)
    expected = manifest['source_inputs']
    if set(inputs) != set(expected):
        raise ValueError(f'AMM source inventory changed: missing={sorted(set(expected)-set(inputs))}, extra={sorted(set(inputs)-set(expected))}')
    tracked = tree_blobs(manifest['source_commit'])
    selected_checkpoint = git('ls-tree', '-r', '--name-only', manifest['source_commit'], '--', 'repro/pump_amm', 'repro/status.json')
    if selected_checkpoint:
        raise ValueError('Pinned source commit unexpectedly contains a selected AMM checkpoint')
    if set(tracked) != set(expected):
        raise ValueError(f'Tracked AMM tree differs from recipe inputs: missing={sorted(set(expected)-set(tracked))}, extra={sorted(set(tracked)-set(expected))}')
    for name, data in inputs.items():
        if sha(data) != expected[name]['sha256']:
            raise ValueError(f'Current source differs from pinned AMM input: {name}')
        if tracked[name] != expected[name]['git_blob']:
            raise ValueError(f'Pinned commit blob differs from AMM input: {name}')
        if git('hash-object', '--', str(ROOT / name)).decode().strip() != tracked[name]:
            raise ValueError(f'Working AMM input differs from pinned Git blob: {name}')

    if {name: sha(data) for name, data in workspace.items()} != manifest['staged_workspace_sha256']:
        raise ValueError('AMM workspace transformation differs from pinned recipe')
    with tempfile.TemporaryDirectory(prefix='amm-recipe-') as temporary:
        staged = Path(temporary) / 'workspace'
        report = recipe.stage(ROOT, staged)
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
