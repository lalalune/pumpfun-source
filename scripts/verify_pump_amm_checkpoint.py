#!/usr/bin/env python3
"""Verify the selected AMM source recipe, saved proof, or its exact fresh replay."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = 'repro/pump_amm/v2-mint-clone-recovery-20261028'
ARTIFACT = CHECKPOINT + '/results/build/candidate.so'
CANDIDATE = 'dbb5dcfd1a1487e22d61ae68d22a9b74087b78a868a08ab974c7bdbb127f1500'
MANIFEST = 'fd4ba56a458aca4090376d75a02f26e4a62153834208189fe82aa59931a9bd8d'


class CheckpointError(Exception):
    pass


def check(ok, msg='checkpoint check failed'):
    # Explicit check instead of `assert`: `python -O` / PYTHONOPTIMIZE strips asserts,
    # which made tampered AMM saved-checkpoint evidence report PASS. (The two newer
    # packet branches already use require(); this covers the saved-checkpoint branch.)
    if not ok:
        raise CheckpointError(msg)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def checkpoint_module(name, path, root):
    # Keep sealed historical builders/verifiers intact, including their hashes.
    reader = module('amm_checkpoint_modules', Path(__file__).with_name('amm_checkpoint_modules.py'))
    return reader.load(name, path, root)


def verify(root=ROOT, runtime=None):
    root = Path(root).resolve()
    selected = json.loads((root / 'repro/status.json').read_text())['pump_amm']
    closure = 'research/amm-layout-closure-20261028'
    if selected['candidate_artifact'] == closure + '/results/build-a/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / closure
        require(sha(packet / 'manifest.json') == selected['checkpoint_manifest_sha256'] == 'f942488a78df7ce4a839fe01ab70112a138eca3979208d83f5d08f511cd836d3', 'AMM layout packet seal')
        report = checkpoint_module('current_amm_layout_closure', packet / 'verify.py', root).verify(root, runtime=runtime, signatures=True)
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']), 'AMM selected layout image')
        require(selected['candidate_symbols_artifact'] == closure + '/results/build-a/symbols.so' and report['symbols_sha256'] == selected['symbols_sha256'] == sha(root / selected['candidate_symbols_artifact']), 'AMM selected layout symbols')
        require(report['normalized'] == selected['normalized_function_matches'] == 784 and report['raw'] == selected['raw_function_matches'] == 784, 'AMM literal window scope')
        require(report['cases'] == selected['validated_cases'] == 17462 and report['signature_fields'] == selected['verified_transaction_signatures'] == 35418, 'AMM current runtime scope')
        require(report['current_source_verified'] and report['cold_dependency_build'] and selected['full_byte_equality'] is False, 'AMM current source/build scope')
        return report
    current = 'repro/pump_amm/canonical-frontier-20261028'
    if selected['candidate_artifact'] == current + '/results/build-a/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / current
        require(sha(packet / 'MANIFEST.json') == 'd05b92a344e1e095e6f68276eb50ddc64a36a0792ac20cb0e7c31c6f6f384489', 'AMM canonical packet seal')
        require(selected['checkpoint_manifest_sha256'] == sha(packet / 'MANIFEST.json'), 'AMM selected packet seal')
        report = checkpoint_module('current_canonical_amm', packet / 'verify.py', root).verify(root, runtime=runtime, signatures=True)
        require(report['status'] == 'PASS', 'AMM current verification')
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']), 'AMM selected candidate')
        require(selected['candidate_symbols_artifact'] == current + '/results/build-a/symbols.so', 'AMM selected symbol path')
        require(report['symbols_sha256'] == selected['symbols_sha256'] == sha(root / selected['candidate_symbols_artifact']), 'AMM selected symbols')
        require(report['current_source_verified'] and report['cold_build_and_repeat_identical'], 'AMM maintained build qualification')
        require(report['normalized'] == selected['normalized_function_matches'] == 784 and report['raw'] == selected['raw_function_matches'] == 394, 'AMM selected window counts')
        require(report['cases'] == selected['validated_cases'] == 17462 and selected['full_byte_equality'] is report['whole_elf_identical'] is False, 'AMM selected finite scope')
        require(report['signature_fields'] == selected['verified_transaction_signatures'] == 35418, 'AMM selected signature scope')
        require(report['canonical_inputs'] == selected['canonical_source_inputs'] == 68 and report['workspace_inputs'] == selected['materialized_workspace_inputs'] == 69, 'AMM selected source scope')
        for key, relative in [('source_recipe', '/workspace_recipe.py'), ('source_builder', '/build.py'), ('source_binding_verifier', '/verify.py'), ('build_log', '/results/build-a/build.log.gz'), ('validation_report', '/results/runtime/audit.json')]:
            require(selected[key] == current + relative and (root / selected[key]).is_file(), 'AMM selected ' + key)
        return report
    check(selected['candidate_artifact'] == ARTIFACT)
    check(selected['candidate_sha256'] == CANDIDATE)
    checkpoint = root / CHECKPOINT
    results = checkpoint / 'results'
    candidate = root / ARTIFACT
    check(sha(candidate) == CANDIDATE and sha(results / 'manifest.json') == MANIFEST)
    allocation = selected['loader_allocation_control']
    allocation_root = root / allocation['proof_path']
    check(sha(allocation_root / 'manifest.json') == allocation['manifest_sha256'])
    allocation_report = module('current_amm_loader_allocation', allocation_root / 'verify.py').verify(allocation_root)
    check(allocation_report['candidate_sha256'] == CANDIDATE)
    check(allocation_report['equal_allocation_control_cases'] == 48)
    check(allocation_report['equal_allocation_control_mismatches'] == 0)
    upgradeable = selected['upgradeable_loader_control']
    upgradeable_root = root / upgradeable['proof_path']
    check(sha(upgradeable_root / 'manifest.json') == upgradeable['manifest_sha256'])
    upgradeable_report = module('current_amm_upgradeable', upgradeable_root / 'verify.py').verify(upgradeable_root)
    check(upgradeable_report['candidate_sha256'] == CANDIDATE)
    check(upgradeable_report['policy_cases'] == 24 and upgradeable_report['policy_mismatches'] == 0)
    if runtime is None:
        # Capture only stdout: the saved verifier's stderr (its failing
        # assertion) must stay visible in the caller's log.
        result = subprocess.run(
            [sys.executable, '-B', str(checkpoint / 'verify_saved.py'), '--current-source'],
            cwd=root, text=True, stdout=subprocess.PIPE, check=True,
        )
        report = json.loads(result.stdout.strip().splitlines()[-1])
        check(report['current_source_checked'] and report['candidate_sha256'] == CANDIDATE)
        return {'status': 'PASS', 'program': 'pump_amm', 'loader_allocation_control': allocation_report, 'upgradeable_loader_control': upgradeable_report, **report}
    entries = json.loads((results / 'manifest.json').read_text())
    check(set(entries) | {'manifest.json'} == {
        str(path.relative_to(results)) for path in results.rglob('*') if path.is_file()
    })
    for name, digest in entries.items():
        check(sha(results / name) == digest, name)
    for name in ['verify_source_binding.py', 'workspace_recipe_v3.py']:
        check(sha(checkpoint / name) == sha(results / 'harness' / name))
    sys.path.insert(0, str(checkpoint))
    try:
        binding = module('selected_amm_source', checkpoint / 'verify_source_binding.py')
        bound = binding.verify(results / 'canonical-source', results / 'source',
                               results / 'build/build-comparison.json', candidate,
                               results / 'build/unstripped.so', results / 'dependency-proof', root)
    finally:
        sys.path.pop(0)
    check(bound['total_compiled_inputs_verified'] == 233 and bound['current_source_verified'])
    dependencies = module('selected_amm_dependencies', results / 'dependency-proof/verify.py')
    check(dependencies.verify(results / 'canonical-source', results / 'build/build-comparison.json')['packages'] == 9)
    runtime = Path(runtime).resolve()
    inputs = json.loads((runtime / 'inputs.json').read_text())
    check(inputs['candidate_sha256'] == CANDIDATE)
    for name, digest in inputs['harness_sha256'].items():
        check(sha(root / name) == digest, name)
    check(inputs['observer_sha256'] == sha(root / 'repro/pump_amm/owner6048-v144/runtime/observe_suite.py'))
    audit = module('selected_amm_audit', checkpoint / 'compare_direct_cached.py')
    report = audit.audit(runtime, CANDIDATE)
    check(report['cases'] == 17462 and not report['mismatches'])
    return {'status': 'PASS', 'program': 'pump_amm', 'candidate_sha256': CANDIDATE, 'loader_allocation_control': allocation_report, 'upgradeable_loader_control': upgradeable_report, **report}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo, args.runtime), indent=2))
