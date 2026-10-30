#!/usr/bin/env python3
"""Verify current selections while retaining P27 as sealed historical evidence.

The P27 catalogue describes its own publication, including old core sources,
script counts and absent files. Those facts are authenticated as history, not
imposed on later reconstructed sources. Current program verifiers establish
the replacement source, artifact, status and saved-signature bindings.
This command performs no build, target execution, network or Git mutation.
"""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)
ROOT = Path(__file__).resolve().parents[1]
RELAY = 'repro/donation-relay/canonical-exact-selection'
P27 = 'repro/layered-passes/pass-27/current-metadata'
P27_SEAL = '52ef5b63cb89c5c8c9c4a25c38f9c556a061ca3b4485ae10495cbecc6f85ab96'
MAYHEM = 'repro/mayhem/initializer-current-20261027'
MAYHEM_SEAL = 'b6b01b400fb7c5ab10db803ba27fe6a76e0e59e9ea7fad25250dc95760cf485c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run_json(root, arguments):
    command = [sys.executable, '-B', *map(str, arguments)]
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{command!r} failed ({result.returncode})\n'
                           f'{result.stdout}\n{result.stderr}')
    # Pump prints its sealed evidence report followed by its current-source
    # report. Retain both rather than silently discarding either record.
    decoder = json.JSONDecoder()
    remaining = result.stdout.strip()
    reports = []
    while remaining:
        report, end = decoder.raw_decode(remaining)
        reports.append(report)
        remaining = remaining[end:].lstrip()
    check(reports and all(isinstance(report, dict) for report in reports), "reconstruction verification failed: reports and all(isinstance(report, dict) for report in reports)")
    return reports


def verify_relay_replay(root):
    """Retain the canonical selection's own 536-record signed replay check."""
    script = root / 'repro/donation-relay/linked-elf-reproduction/verify.py'
    result = subprocess.run([sys.executable, '-B', str(script)], cwd=root,
                            text=True, capture_output=True, check=True)
    return {'status': 'PASS', 'saved_verifier': str(script.relative_to(root)),
            'stdout': result.stdout, 'stderr': result.stderr,
            'new_target_executions': 0}


def verify(root):
    root = Path(root).resolve()
    initial_status = read(root / 'repro/status.json')
    relay_directory = root / RELAY
    sys.path.insert(0, str(relay_directory))
    try:
        selection = module('current_publication_relay_selection',
                           relay_directory / 'verify_selection.py')
        selection.authenticate()
        bridge = module('current_relay_scanner_bridge', root / 'research/all-contract-completion-20261028/relay/verify_current_bridge.py')
        relay_transition = bridge.verify(root)
        relay = relay_transition['current_selection']
        check(relay['verified'] and relay['canonical_source60_verified'], "reconstruction verification failed: relay['verified'] and relay['canonical_source60_verified']")
        check(relay['all492_raw'] and relay['meaningful_elf_literal_equal'], "reconstruction verification failed: relay['all492_raw'] and relay['meaningful_elf_literal_equal']")
        check(relay['selected_payload_literal_checked'], "reconstruction verification failed: relay['selected_payload_literal_checked']")

        historical = module('current_publication_p27_history',
                            relay_directory / 'common.py')
        context = historical.metadata_context(root, root / P27, P27_SEAL)
        catalogue = context.catalogue()
        context.unchanged(root / P27)
        check(len(catalogue) == 53, "reconstruction verification failed: len(catalogue) == 53")

        # Preserve the old Fees source map only while that historical selection
        # is current. Exact canonical promotion has its own complete source gate.
        if initial_status['pump_fees']['candidate_artifact'] != 'research/all-contract-completion-20261028/fees-built/canonical-01/candidate.so':
            fees = context.F['compiled']['pump_fees']
            layout = context.R['source_layout']['pump_fees']
            names = historical.source_names(
                root / layout['crate'], root / layout['workspace'], root,
                [root / name for name in layout.get('extra_inputs', [])])
            check(names == set(fees['source']), 'Fees source inventory changed')
            check(initial_status['pump_fees'] == context.F['status']['pump_fees'], "reconstruction verification failed: initial_status['pump_fees'] == context.F['status']['pump_fees']")
    finally:
        sys.path.pop(0)

    relay_repeat = root / 'research/relay-current-repeat-20261028'
    if sha(relay_repeat / 'manifest.json') != 'ad2353dec21a94f5d9a202e956d95b112f3130420301988399c845b8122aaea3':
        raise ValueError('Current Relay repeat packet seal')
    relay_repeat_report = run_json(root, [relay_repeat / 'verify.py', '--repo', root])[-1]
    if not relay_repeat_report['meaningful_elf_equal'] or not relay_repeat_report['genuine_loader_payload_equal']:
        raise ValueError('Current Relay repeat qualification')

    mayhem_directory = root / MAYHEM
    check(sha(mayhem_directory / 'manifest.json') == MAYHEM_SEAL, "reconstruction verification failed: sha(mayhem_directory / 'manifest.json') == MAYHEM_SEAL")
    manifest = read(mayhem_directory / 'manifest.json')['files']
    actual = {str(path.relative_to(mayhem_directory))
              for path in mayhem_directory.rglob('*') if path.is_file()}
    check(actual == set(manifest) | {'manifest.json'}, "reconstruction verification failed: actual == set(manifest) | {'manifest.json'}")
    for name, digest in manifest.items():
        path = mayhem_directory / name
        check(not path.is_symlink() and sha(path) == digest, name)
    stats = read(mayhem_directory / 'stats.json')
    status = initial_status['mayhem']
    if status['candidate_artifact'] == 'research/mayhem-canonical-promotion-20261028/hosted/40770208958/candidate.so':
        mayhem_command = [root / 'scripts/verify_mayhem_checkpoint.py', '--repo', root]
    else:
        check(status['candidate_artifact'] == MAYHEM + '/candidate.so', "reconstruction verification failed: status['candidate_artifact'] == MAYHEM + '/candidate.so'")
        check(status['candidate_sha256'] == stats['candidate_sha256'], "reconstruction verification failed: status['candidate_sha256'] == stats['candidate_sha256']")
        check(status['candidate_symbols_artifact'] == MAYHEM + '/unstripped.so', "reconstruction verification failed: status['candidate_symbols_artifact'] == MAYHEM + '/unstripped.so'")
        check(sha(root / status['candidate_symbols_artifact']) == stats['unstripped_sha256'], "reconstruction verification failed: sha(root / status['candidate_symbols_artifact']) == stats['unstripped_")
        check(status['comparison_report'] == MAYHEM + '/comparison.json', "reconstruction verification failed: status['comparison_report'] == MAYHEM + '/comparison.json'")
        check(status['full_byte_equality'] is False, "reconstruction verification failed: status['full_byte_equality'] is False")
        mayhem_command = [mayhem_directory / 'verify.py', '--current-source', root,
                          '--expected-seal', MAYHEM_SEAL]

    commands = {
        'pump': [root / 'scripts/verify_pump_main_checkpoint.py', '--repo', root],
        'pump_amm': [root / 'scripts/verify_pump_amm_checkpoint.py', '--repo', root],
        'pump_fees': [root / 'scripts/verify_current_checkpoint.py', 'pump_fees', '--repo', root],
        'mayhem': mayhem_command,
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {name: executor.submit(run_json, root, command)
                   for name, command in commands.items()}
        replay = executor.submit(verify_relay_replay, root)
        verified = {name: future.result() for name, future in futures.items()}
        relay_replay = replay.result()
    for name, reports in verified.items():
        last = reports[-1]
        check(last.get('status') == 'PASS' or last.get('passed') is True, name)
        check(last['candidate_sha256'] == initial_status[name]['candidate_sha256'], name)
    check(read(root / 'repro/status.json') == initial_status, 'Selections changed during verification')
    return {
        'status': 'PASS_CURRENT_RECONSTRUCTION',
        'current_source_and_artifact_reports': verified,
        'relay': relay,
        'relay_scanner_transition': relay_transition,
        'relay_maintained_repeat': relay_repeat_report,
        'relay_saved_replay': relay_replay,
        'historical_p27': {
            'metadata_manifest_sha256': P27_SEAL,
            'catalogue_packages_authenticated': len(catalogue),
            'unchanged_metadata_payloads_authenticated': True,
            'scope': 'Sealed historical data; old source107, script counts and absence rules are not current requirements.',
        },
        'new_builds': 0,
        'new_target_executions': 0,
        'historical_source_recipe_proven': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo), indent=2))
