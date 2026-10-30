#!/usr/bin/env python3
"""Offline frozen6a artifact/source/score replay; never invokes a compiler or network."""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qualification as q

BASE = '6a1d23a306ce0b2213aac937d7a81472efe5986b'
CONTROLLER = '2e208af56710ddfa404cd9dffacc2069580d27fb'
ARCHIVE = 'd3bfd56530ba9aa5fe0a0a3681bc1db20d34269ff4fcf08a472847a41cc6afbf'
RUNNER = 'reconstruction/pump-main/lanes/current-native-control/pump_current_control.py'
WORKFLOW = '.github/workflows/qualify-pump-macos-v144.yml'


def git_hash(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    q.need(bool(name) and not p.is_absolute() and '\\' not in name
           and all(v not in ('', '.', '..') for v in name.split('/')), 'unsafe archive path')
    return p


class GitProof:
    """Verify raw commits/trees; resolve leaves without Git or branch-name trust."""
    def __init__(self, document):
        q.need(document['schema'] == 'pump-checkpoint-git-proof-v1', 'Git proof schema differs')
        self.objects = {}
        self.roots = {}
        for oid, row in document['objects'].items():
            kind = row['type']
            q.need(kind in ('commit', 'tree'), 'unexpected Git object type')
            data = base64.b64decode(row['base64'], validate=True)
            q.need(git_hash(kind, data) == oid, 'Git object hash differs')
            self.objects[oid] = (kind, data)
        for commit in (BASE, CONTROLLER):
            kind, data = self.objects[commit]
            q.need(kind == 'commit' and data.startswith(b'tree '), 'invalid Git commit')
            self.roots[commit] = data.split(b'\n', 1)[0][5:].decode('ascii')
        q.need(self.roots == document['roots'], 'Git root binding differs')
        for commit, paths in document['bindings'].items():
            q.need(commit in self.roots, 'untrusted commit binding')
            for path, row in paths.items():
                q.need(self.lookup(commit, path) == (row['mode'], row['gitBlob']),
                       f'Git leaf binding differs: {path}')

    def tree(self, oid):
        kind, data = self.objects[oid]
        q.need(kind == 'tree', 'expected Git tree')
        out, i = {}, 0
        while i < len(data):
            end = data.index(b'\0', i)
            mode, name = data[i:end].split(b' ', 1)
            q.need(end + 21 <= len(data), 'truncated Git tree')
            name, mode = name.decode('utf-8'), mode.decode('ascii')
            q.need(name not in out and '/' not in name and name not in ('.', '..'), 'invalid Git tree name')
            out[name] = (mode, data[end + 1:end + 21].hex())
            i = end + 21
        return out

    def lookup(self, commit, path):
        safe_name(path)
        mode, oid = '40000', self.roots[commit]
        for part in path.split('/'):
            q.need(mode == '40000', 'non-directory Git ancestor')
            mode, oid = self.tree(oid)[part]
        return mode, oid

    def leaves(self, commit, prefix):
        mode, oid = self.lookup(commit, prefix)
        q.need(mode == '40000', 'source root is not a tree')
        out = {}
        def walk(root, address):
            for name, (m, o) in self.tree(address).items():
                path = root + '/' + name
                if m == '40000': walk(path, o)
                else: out[path] = (m, o)
        walk(prefix, oid)
        return out


def unpack_tar(data, root, expected=None):
    seen = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            safe_name(member.name)
            q.need(member.isfile() and member.mode == 0o644 and member.name not in seen,
                   'unexpected tar type/mode/duplicate')
            q.need(member.size <= 4_000_000, 'oversized tar member')
            value = archive.extractfile(member).read()
            seen[member.name] = {'bytes': len(value), 'sha256': q.sha(value)}
            if expected is not None:
                q.need(member.name in expected and seen[member.name] == expected[member.name],
                       'tar content differs')
            target = root / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(value)
    if expected is not None: q.need(seen == expected, 'tar member set differs')
    return seen


def unpack_zip(path, root, expected):
    q.need(q.sha(path.read_bytes()) == ARCHIVE, 'native archive SHA256 differs')
    seen = {}
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            safe_name(member.filename)
            q.need(not member.is_dir() and member.filename not in seen, 'unexpected ZIP member')
            q.need(not stat.S_ISLNK(member.external_attr >> 16) and member.file_size < 5_000_000,
                   'invalid ZIP type/size')
            value = archive.read(member)
            seen[member.filename] = {'bytes': len(value), 'sha256': q.sha(value)}
            q.need(member.filename in expected and seen[member.filename] == expected[member.filename],
                   'native archive member differs')
            target = root / member.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(value)
    q.need(seen == expected, 'native archive member set differs')


def local_map(root, expected):
    """Explicit supplied root: absent/changed bytes fail, never trigger fallback."""
    for name, digest in expected.items():
        safe_name(name)
        p = root / name
        q.need(p.is_file() and q.sha(p.read_bytes()) == digest, f'local input absent/different: {name}')
    return {'status': 'PASS', 'files': len(expected)}


def sdk_check(root, inventory):
    entries = inventory['entries']
    observed = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_symlink() or p.is_file()}
    q.need(observed == set(entries), 'local SDK file/symlink set differs')
    for name, row in entries.items():
        safe_name(name)
        p = root / name
        if row['type'] == 'symlink':
            q.need(p.is_symlink() and os.readlink(p) == row['target'], f'SDK symlink differs: {name}')
        else:
            q.need(not p.is_symlink() and p.is_file() and p.stat().st_size == row['bytes']
                   and q.sha(p.read_bytes()) == row['sha256']
                   and stat.S_IMODE(p.stat().st_mode) == int(row['mode'], 8), f'SDK file differs: {name}')
    return {'status': 'PASS', 'entries': len(entries)}


def execute(packet, original, args):
    metadata = q.read_json(packet / 'CHECKPOINT.json')
    q.need(metadata['sourceCommit'] == BASE and metadata['controllerCommit'] == CONTROLLER,
           'checkpoint commit differs')
    q.need(metadata['artifactZip']['sha256'] == ARCHIVE
           and metadata['run'] == 41003848803 and metadata['artifactId'] == 12954757170,
           'hosted artifact pin differs')
    proof_bytes = (packet / 'git-proof.json').read_bytes()
    q.need(q.sha(proof_bytes) == metadata['gitProofSha256'], 'Git proof SHA256 differs')
    proof = GitProof(q.read_json(packet / 'git-proof.json'))
    q.need(q.sha(original.read_bytes()) == q.ORIGINAL, 'captured original SHA256 differs')
    q.need(git_hash('blob', original.read_bytes()) == proof.lookup(BASE, 'evidence/original/pump/deployed.so')[1],
           'original Git blob differs')
    with tempfile.TemporaryDirectory(prefix='pump-native-checkpoint-') as temp:
        temp = Path(temp)
        repo, artifact, output = temp / 'inputs', temp / 'artifact', temp / 'analysis'
        repo.mkdir(); artifact.mkdir(); output.mkdir()
        archive = packet / 'native-artifact.zip'
        q.need(archive.stat().st_size == metadata['artifactZip']['bytes'], 'ZIP size differs')
        unpack_zip(archive, artifact, metadata['artifactMembers'])
        frozen = (packet / 'frozen-inputs.tar.gz').read_bytes()
        q.need(q.sha(frozen) == metadata['frozenInputs']['sha256'], 'frozen input archive differs')
        unpack_tar(frozen, repo, metadata['frozenInputs']['members'])
        unpack_tar((artifact / 'program-source.tar.gz').read_bytes(), repo)
        for path in metadata['frozenInputs']['members']:
            head, name = (CONTROLLER, path[11:]) if path.startswith('controller/') else (BASE, path)
            q.need(git_hash('blob', (repo / path).read_bytes()) == proof.lookup(head, name)[1],
                   f'frozen input not in pinned Git tree: {path}')
        # The original is supplied explicitly. Other unbundled binaries are optional.
        p = repo / 'evidence/original/pump/deployed.so'
        p.parent.mkdir(parents=True, exist_ok=True); p.symlink_to(original.resolve())
        q.need(set(metadata['unbundledToolchainPaths']) ==
               {r['path'] for r in q.read_json(artifact / 'toolchain-source-inputs.json')['files']}
               - set(metadata['frozenInputs']['members']), 'unbundled inventory differs')
        if args.toolchain_inputs is not None:
            for name in metadata['unbundledToolchainPaths']:
                if name == 'evidence/original/pump/deployed.so': continue
                source = args.toolchain_inputs / name
                q.need(source.is_file(), f'explicit toolchain input missing: {name}')
                dest = repo / name; dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to(source.resolve())
        q.PROOF, q.HEAD = proof, BASE
        q.UNVERIFIED_TOOLCHAIN.clear()
        options = SimpleNamespace(repo=repo, original=original, artifact_dir=artifact,
            controller_head=CONTROLLER, runner_git_path=RUNNER, workflow_git_path=WORKFLOW,
            output=output, inspect_only=False)
        result = q.run(options)
        q.need(result['current_summary'] == metadata['summary'], 'frozen summary differs')
        remaining = [hex(int(k)) for k, r in q.read_json(artifact / 'score.json')['windows'].items()
                     if not r['normalized']]
        q.need(set(remaining) == set(metadata['remaining']), 'remaining-window set differs')
        toolmap = q.read_json(artifact / 'tool-inputs.json')
        sdk = q.read_json(repo / 'reconstruction/toolchain/v1.44-macos-inventory.json')
        for suffix, member in [('rust/bin/rustc', 'rust/bin/rustc'), ('rust/bin/cargo', 'rust/bin/cargo'),
                               ('llvm/bin/llvm-objcopy', 'llvm/bin/llvm-objcopy')]:
            matches = [v for k,v in toolmap.items() if k.endswith('v1.44/platform-tools/' + suffix)]
            q.need(matches == [sdk['entries'][member]['sha256']], 'recorded native SDK pin differs')
        skipped = {'status': 'NOT RUN', 'reason': 'no explicit local input root supplied'}
        registry = q.read_json(artifact / 'registry-source-inputs.json')
        q.need(len(registry) == 8390, 'registry input count differs')
        external = {
            'native_sdk_physical_bytes': sdk_check(args.sdk_root, sdk) if args.sdk_root else skipped,
            'registry_physical_bytes': local_map(args.registry_source, registry) if args.registry_source else skipped,
            'unbundled_toolchain_bytes': {'status': 'NOT RUN' if q.UNVERIFIED_TOOLCHAIN else 'PASS',
                'unverified_paths': sorted(q.UNVERIFIED_TOOLCHAIN),
                'reason': 'Git leaf identities/recorded hashes verified; absent bytes are not independently rehashed'}
        }
        q.need(not args.require_local_inputs or all(v['status'] == 'PASS' for v in external.values()),
               'required physical SDK/registry/toolchain qualification was not completed')
        return {'ok': True, 'checkpoint': BASE, 'controller': CONTROLLER,
            'archive_sha256': ARCHIVE, 'artifact_integrity': 'PASS', 'source_files': result['source_files'],
            'compiled_workspace_files': result['compiled_workspace_files'],
            'builder_source_sha256': result['actual_builder_source_sha256'],
            'summary': result['current_summary'], 'remaining': metadata['remaining'],
            'memberships': q.read_json(output / 'memberships.json'),
            'focus_residuals': result['focus_summary'],
            'whole_original_elf_equal': {'stripped': result['stripped_original_elf_equal'],
                                         'unstripped': result['unstripped_original_elf_equal']},
            'external_qualification': external,
            'limits': ['Frozen6a checkpoint, not latest main.',
                'No compiler, runtime, transaction or new Rust recovery performed by replay.',
                'Git object hashes authenticate pinned tree content, not signatures or legal authorship.',
                'Hosted-run identity is retained provenance, not an offline network attestation.',
                'Normalized bodies do not establish whole-program identity.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True, type=Path, help='captured deployed.so (exact hash required)')
    parser.add_argument('--sdk-root', type=Path, help='native macOS v1.44 platform-tools root; full2785 inventory')
    parser.add_argument('--registry-source', type=Path, help='Cargo registry/src root, including index.crates.io-*')
    parser.add_argument('--toolchain-inputs', type=Path, help='frozen6a repo projection for unbundled binaries')
    parser.add_argument('--require-local-inputs', action='store_true')
    parser.add_argument('--report', type=Path, help='optional NEW detailed JSON file; existing output refused')
    args = parser.parse_args()
    try:
        q.need(args.report is None or not args.report.exists(), 'report output already exists')
        result = execute(Path(__file__).resolve().parent, args.original.resolve(), args)
        if args.report:
            with args.report.open('x') as stream: json.dump(result, stream, sort_keys=True, indent=2); stream.write('\n')
        print(json.dumps({k:v for k,v in result.items() if k not in ('memberships','focus_residuals')},sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, tarfile.TarError) as error:
        print(json.dumps({'ok':False,'error':str(error)}),file=sys.stderr)
        return 1


if __name__ == '__main__': sys.exit(main())
