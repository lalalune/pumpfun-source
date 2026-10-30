#!/usr/bin/env python3
"""Authenticate restored public recipe inputs and an optional real Mayhem stage."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
MANIFEST_SHA256 = '977c888f1d57b9609d2c6cca8b881fbab036a6a6aa1e8835dee145e79e7b2693'
ENTRYPOINT_SHA256 = 'e6ff50da38e45d1d2a843bc5f2407e265c84643a2daa5a67ef6376df3c2ae595'
PUBLIC_COMMIT = 'decb244ccf8a81b086e940568a2d03336309046f'
sha = lambda b: hashlib.sha256(b).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def regular(root, name):
    relative = PurePosixPath(name)
    require(name and not relative.is_absolute() and '..' not in relative.parts
            and relative.as_posix() == name and '\\' not in name, 'invalid input path')
    path = root
    for part in relative.parts:
        path = path / part
        require(not path.is_symlink(), 'symlink in input path: ' + name)
    require(path.is_file(), 'missing regular input: ' + name)
    return path


def verify(repository, staged=None):
    manifest_bytes = regular(repository, 'reconstruction/mayhem/recovered-stage-inputs.json').read_bytes()
    require(sha(manifest_bytes) == MANIFEST_SHA256, 'recovery manifest changed')
    manifest = json.loads(manifest_bytes)
    require(manifest['public_source_commit'] == PUBLIC_COMMIT, 'public source commit changed')
    records = manifest['files']
    require(len(records) == len({r['path'] for r in records}) == 101, 'recovery file set changed')
    for row in records:
        data = regular(repository, row['path']).read_bytes()
        require(len(data) == row['bytes'] and sha(data) == row['sha256'], 'restored bytes differ: ' + row['path'])
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(blob == row['source_git_blob'], 'public Git blob differs: ' + row['path'])
    policy = manifest['checkout_policy']
    require(policy['path'] == 'research/mayhem-fresh-host-20261028/.gitattributes', 'checkout policy path differs')
    policy_bytes = regular(repository, policy['path']).read_bytes()
    require(policy_bytes == b'* -text\n' and len(policy_bytes) == policy['bytes']
            and sha(policy_bytes) == policy['sha256'], 'checkout byte-preservation policy differs')
    require(hashlib.sha1(b'blob ' + str(len(policy_bytes)).encode() + b'\0' + policy_bytes).hexdigest()
            == policy['source_git_blob'], 'public checkout-policy blob differs')
    entrypoint = regular(repository, 'programs/mayhem/build_exact.py')
    require(sha(entrypoint.read_bytes()) == ENTRYPOINT_SHA256, 'maintained entrypoint changed')
    result = {'public_source_commit': PUBLIC_COMMIT, 'restored_inputs': len(records),
              'checkout_policies': 1,
              'stage_checked': staged is not None, 'fresh_compilation_checked': False,
              'fresh_elf_equality_checked': False}
    if staged is None:
        return result
    recipe = staged / 'recipe'
    record = json.loads(regular(staged, 'source-mapping.json').read_bytes())
    require(record['stage_only'] is True and record['compiler_executed'] is False
            and record['target_executed'] is False, 'not a stage-only receipt')
    require(record['source_files'] == 67 and record['allocation_tail_emitted'] is False,
            'source count or allocation-tail claim changed')
    require(record['wrapper_sha256'] == record['source_entrypoint_sha256'] == ENTRYPOINT_SHA256,
            'entrypoint receipt differs')
    support = repository / 'research/mayhem-linker-locators-20261028'
    pins = json.loads((support / 'inputs.json').read_bytes())
    require(record['stager_script_sha256'] == pins['source_builder_parent_sha256'], 'sealed stager receipt differs')
    expected_source = json.loads((repository / 'research/mayhem-fresh-host-20261028/controller/source-inputs.json').read_bytes())['source_files']
    expected = {row['path']: row['sha256'] for row in expected_source}
    require(len(expected) == 67 and record['canonical_inputs'] == expected and set(record['mapping']) == set(expected),
            'canonical source inventory differs')
    for name, digest in expected.items():
        source = regular(repository / 'programs/mayhem', name).read_bytes()
        compressed = regular(recipe / 'controller/sources', name + '.gz').read_bytes()
        require(sha(source) == digest and gzip.decompress(compressed) == source, 'staged source differs: ' + name)
        require(record['mapping'][name] == {'canonical_sha256': digest, 'staged_raw_sha256': digest},
                'source mapping differs: ' + name)
    actual = {p.relative_to(recipe).as_posix(): sha(p.read_bytes()) for p in recipe.rglob('*') if p.is_file()}
    require(actual == record['copied_recipe_inputs'], 'staged recipe inventory differs')
    prefix = 'research/mayhem-fresh-host-20261028/'
    recipe_rows = {r['path'][len(prefix):]: r for r in records if r['path'].startswith(prefix)}
    require(len(recipe_rows) == 98 and set(actual) == set(recipe_rows), 'staged recipe file set differs')
    for name, row in recipe_rows.items():
        require(not (recipe / name).is_symlink(), 'staged symlink: ' + name)
        if name == 'controller/ordered-native.ld':
            require(actual[name] == pins['derived_script_sha256'], 'derived script differs')
        elif not name.startswith('controller/sources/'):
            require(actual[name] == row['sha256'], 'sealed recipe file differs: ' + name)
    require(record['linker_locator_transform'] == {
        'parent_sha256': pins['parent_script_sha256'], 'derived_sha256': pins['derived_script_sha256'],
        'changed_selectors': pins['changed_selectors'], 'input_sections_or_order_changed': False,
        'cargo_artifact_filename_digests_only': True}, 'locator transformation receipt differs')
    result.update(source_files=67, recipe_files=98, compiler_executed=False, target_executed=False)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=HERE.parents[1])
    p.add_argument('--stage', type=Path)
    args = p.parse_args()
    print(json.dumps(verify(args.repo.resolve(), args.stage.resolve() if args.stage else None), indent=2))


if __name__ == '__main__':
    main()
