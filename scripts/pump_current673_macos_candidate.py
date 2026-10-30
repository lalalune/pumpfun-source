#!/usr/bin/env python3
"""Measure one frozen source proposal with the current673 native cold recipe."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
import argparse
import ast
import copy
import difflib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile

import pump_current673_macos_control as control

ROOT = control.ROOT
DIRECTORY = ROOT / 'research/pump-current673-macos-qualification/candidates'


def descriptor(name, source_directory=None):
    spec, cold, source, manifest, expected = control.inspect(source_directory)
    ledger = json.loads((DIRECTORY / 'descriptors.json').read_text())
    proposal = ledger['proposals'][name]
    assert expected['source_inputs'][proposal['source_path']] == proposal['before_sha256']
    frozen = DIRECTORY / proposal['frozen_file']
    assert frozen.parent == DIRECTORY and frozen.suffix == '.rs'
    assert control.sha(frozen) == proposal['after_sha256']
    changed = copy.deepcopy(expected)
    changed['source_inputs'][proposal['source_path']] = proposal['after_sha256']
    assert [key for key in manifest if manifest[key] != changed['source_inputs'][key]] == [proposal['source_path']]
    original = (cold / 'build.py').read_text()
    terminal = ";assert record['qualified_image_hashes_equal']\n"
    assert original.endswith(terminal) and original.count(terminal) == 1
    # The candidate has no preselected output hash. Keep the exact control hash
    # comparison in the receipt, but make its terminal assertion measurement-only.
    derived = original[:-len(terminal)] + '\n'
    ast.parse(derived)
    patch = ''.join(difflib.unified_diff(original.splitlines(True), derived.splitlines(True),
                                        fromfile='frozen-control-build.py', tofile='candidate-measurement-build.py'))
    return spec, cold, source, ledger, proposal, frozen, changed, derived, patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=['cto', 'sweep', 'perhop', 'sell-event', 'constructor', 'cto-used-flow', 'perhop-clock', 'sweep-read-timing'], required=True)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--source-directory', type=Path, default=control.SOURCE_DIRECTORY,
                        help='Archived673 primary source; all65 existing hashes must match')
    args = parser.parse_args()
    spec, cold, source, ledger, proposal, frozen, expected, derived, patch = descriptor(args.candidate, args.source_directory)
    if args.inspect:
        print(json.dumps({'candidate': args.candidate, 'proposal': proposal, 'adapter_patch': patch}, indent=2))
        return
    assert platform.system() == 'Darwin' and platform.machine() == 'arm64'
    assert sys.version_info >= (3, 12)
    # The pinned official action retrieves the exact prior control artifact.
    # Authenticate the actual reproduced ELFs, source-bound builder and host head;
    # no unauthenticated shared-runner GitHub API quota is required here.
    proof = ROOT / 'work/pump-current673-control-proof'
    proof_manifest = json.loads((proof / 'MANIFEST.json').read_text())
    for name, digest in proof_manifest.items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert control.sha(proof / relative) == digest
    result = json.loads((proof / 'RESULT.json').read_text())
    host = json.loads((proof / 'host.json').read_text())
    assert result['status'] == 'reproduced' and host['revision'] == ledger['control_head']
    assert result['base_commit'] == spec['base_commit'] and result['cold_empty_target']
    assert control.sha(proof / 'executed-builder.py') == spec['builder_sha256']
    for field, filename in [('candidate_sha256', 'candidate.so'), ('unstripped_sha256', 'unstripped.so')]:
        assert result[field] == spec['expected'][field] == control.sha(proof / filename)
    control.WORK = ROOT / ('work/pump-current673-macos-' + args.candidate)
    control.EVIDENCE = control.WORK / 'evidence'
    evidence, work = control.EVIDENCE, control.WORK
    evidence.mkdir(parents=True, exist_ok=False)
    control.write(evidence / 'control-proof.json', {'run_id': ledger['control_run'],
                  'artifact_name': 'pump-current673-native-control-' + str(ledger['control_run']) + '-1',
                  'manifest_sha256': control.sha(proof / 'MANIFEST.json'), 'result': result, 'host': host})
    control.write(evidence / 'proposal.json', proposal)
    control.write(evidence / 'inputs.json', spec)
    control.write(evidence / 'candidate-build-inputs.json', expected)
    control.write(evidence / 'host.json', {'system': platform.system(), 'machine': platform.machine(),
                  'python': sys.version, 'primary_source_directory': str(source), 'revision': subprocess.check_output(
                      ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()})
    (evidence / 'measurement-adapter.patch').write_text(patch)
    shutil.copyfile(Path(__file__), evidence / 'candidate-controller.py')
    shutil.copyfile(Path(control.__file__), evidence / 'control-controller.py')
    shutil.copyfile(ROOT / '.github/workflows/qualify-pump-macos-v144.yml', evidence / 'workflow.yml')
    shutil.copyfile(cold / 'build.py', evidence / 'frozen-control-build.py')
    shutil.copyfile(frozen, evidence / 'proposed-source.rs')
    shutil.copyfile(DIRECTORY / 'descriptors.json', evidence / 'descriptors.json')
    build = work / 'build'
    try:
        # An isolated repository root preserves the frozen builder's relative
        # source projection. Only the declared one-file source substitution and
        # the explicit terminal measurement assertion differ from the control.
        package = work / 'research/cold'
        package.mkdir(parents=True)
        (package / 'build.py').write_text(derived)
        control.write(package / 'build-inputs.json', expected)
        shutil.copytree(cold / 'tools', package / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
        staged = work / 'source'
        for name, digest in expected['source_inputs'].items():
            destination = staged / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(frozen if name == proposal['source_path'] else source / name, destination)
            assert control.sha(destination) == digest
        original = work / 'evidence/original/pump/deployed.so'
        original.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'evidence/original/pump/deployed.so', original)
        assert control.sha(original) == spec['original_sha256']
        downloads = {}
        for label, pin in spec['archives'].items():
            archive_path = work / (label + '.tar.bz2')
            control.download_archive(pin['url'], pin['sha256'], archive_path)
            destination = work / label
            destination.mkdir()
            with tarfile.open(archive_path) as archive:
                archive.extractall(destination, filter='data')
            downloads[label] = dict(pin, observed_sha256=control.sha(archive_path))
            control.write(evidence / 'downloads.json', downloads)
        sdk = work / 'macos'
        registry = work / 'cargo-home'
        libraries = work / 'linux/rust/lib/rustlib/sbpf-solana-solana/lib'
        env = dict(os.environ, CARGO_HOME=str(registry), RUSTC=str(sdk / 'rust/bin/rustc'),
                   PATH=str(sdk / 'rust/bin') + os.pathsep + os.environ['PATH'])
        control.run('fetch', [sdk / 'rust/bin/cargo', 'fetch', '--locked', '--manifest-path', staged / 'Cargo.toml'], env)
        control.run('candidate-build', [sys.executable, '-B', package / 'build.py', '--source-directory', staged,
                    '--sdk', sdk, '--cargo-home', registry, '--target-library-profile', 'linux-v1.44-sbpf',
                    '--target-libraries', libraries, '--wrapper', package / 'tools/pump_physical_source_wrapper.py', '--output', build])
        record = json.loads((build / 'build-attempt.json').read_text())
        assert all(record[k] for k in ['cold_empty_target', 'source_unchanged', 'tools_unchanged',
                    'sdk_rust_libraries_unchanged', 'registry_sources_unchanged', 'target_libraries_unchanged'])
        assert record['tool_sha256'] == expected['tool_sha256']
        log = (build / 'build.log').read_text()
        assert '--crate-name pump_recovered ' in log and '--crate-name pump_token_ext ' in log
        assert control.inspect(source)[3] == spec_source_inputs(cold)
        control.write(evidence / 'RESULT.json', {'status': 'compiled-measurement-only', 'candidate': args.candidate,
                      'base_commit': spec['base_commit'], 'control_run': ledger['control_run'], 'proposal': proposal,
                      'candidate_sha256': control.sha(build / 'candidate.so'), 'unstripped_sha256': control.sha(build / 'unstripped.so'),
                      'control_hashes_equal': record['qualified_image_hashes_equal'], 'cold_empty_target': True,
                      'both_local_crates_compiled': True,
                      'limits': 'No acceptance, census gain, runtime behavior or original whole-ELF identity claim.'})
        print((evidence / 'RESULT.json').read_text(), flush=True)
    finally:
        control.retain(build)


def spec_source_inputs(cold):
    return json.loads((cold / 'build-inputs.json').read_text())['source_inputs']


if __name__ == '__main__':
    main()
