#!/usr/bin/env python3
"""Verify the selected main-Pump source against its sealed, reproduced checkpoint."""
import argparse
import hashlib
import json
from pathlib import Path
from build_source_manifest import source_manifest
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'repro/pump/main-contract-round47-20261027'
MANIFEST_SHA256 = '6f947fcbb1299a7ba106b814d03d1256f3a89c802a33384291f569980fffc405'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    root = Path(root).resolve()
    selected = json.loads((root / 'repro/status.json').read_text())['pump']
    notice = 'research/pump-program-creator-notice-qualification-20261028'
    if selected['candidate_artifact'] == notice + '/artifacts/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / notice
        seal = 'ef50bb5262f67c59f4d1850f83e2821fa1e9c5f02649589cab356a6e28cffb49'
        require(len(seal) == 64 and all(c in '0123456789abcdef' for c in seal), 'Pump program-creator notice final seal is not frozen')
        require(sha(packet / 'MANIFEST.json') == selected['candidate_packet_manifest_sha256'] == selected['checkpoint_manifest_sha256'] == seal, 'Pump notice qualification seal')
        result = subprocess.run([sys.executable, '-B', str(packet / 'verify.py'), '--source-directory', str(root / 'programs/pump')], cwd=root, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        require(report['passed'] and report['sealed'], 'Pump sealed notice qualification')
        candidate = 'd0377d7cef5b7378063f8bfabac5dc9c08d29eeaaaaa14022d36909688ff5e1b'
        symbols = '0f50faa8c325104dc77898ed84866dec2ad1eec475b6abba72c475cf7bf9bab6'
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']) == candidate, 'Pump notice selected executable')
        require(selected['candidate_symbols_artifact'] == notice + '/artifacts/unstripped.so' and selected['symbols_sha256'] == sha(root / selected['candidate_symbols_artifact']) == symbols, 'Pump notice selected symbols')
        require(sha(packet / 'SOURCE65.json') == '61e9741da82f4bc28dcfa25c78e0160f25d9eaeb9c95e9b1d0af52e13a972003', 'Pump notice exact source65 map')
        require(selected['canonical_source_inputs'] == len(json.loads((packet / 'SOURCE65.json').read_text())) == 65 and selected['materialized_workspace_inputs'] == 66, 'Pump notice compiler source scope')
        require(report['normalized'] == selected['normalized_function_matches'] == 1019 and report['raw'] == selected['raw_function_matches'] == 188 and report['window_gain'] == 0, 'Pump unchanged complete-window scope')
        require(report['actual_builds'] == 2 and report['cold_empty_target'] and selected['portable_empty_target_build'], 'Pump actual matching warm and cold builds')
        full, focus, captured = report['full44'], report['focused'], report['captured_create']
        require(full['pairs'] == selected['validated_cases'] == 10468 and full['transaction_fields'] == selected['runtime_transaction_fields'] == 18343 and full['signature_fields'] == selected['verified_transaction_signatures'] == 27875, 'Pump notice full runtime scope')
        require(focus['strict_case_records'] == selected['focused_runtime_cases'] == 106 and focus['strict_outcome_executions'] == selected['focused_runtime_transactions'] == 318 and focus['strict_signature_fields_verified'] == selected['focused_runtime_signature_fields'] == 465, 'Pump notice focused scope')
        require(focus['legacy_case_pairs'] == selected['legacy_runtime_cases'] == 284 and focus['legacy_signature_fields_verified'] == selected['legacy_runtime_signature_fields'] == 568, 'Pump notice legacy scope')
        require(focus['extension_case_pairs'] == selected['extension_runtime_cases'] == 126 and focus['extension_signature_fields_verified'] == selected['extension_runtime_signature_fields'] == 252, 'Pump notice extension scope')
        require(captured['cases'] == selected['captured_create_cases'] == 14 and captured['executions'] == captured['actual_captured_loads'] == 42 and captured['signature_fields'] == selected['captured_create_signature_fields'] == 84 and captured['source_normalization'] is None, 'Pump notice captured creation supplement')
        require(selected['captured_create_packet_manifest_sha256'] == seal and report['counter_cases'] == selected['accrual_counter_cases'] == 12 and report['counter_executions'] == selected['accrual_counter_executions'] == 36 and report['parent_Source_differences'] == 3 and report['source_normalization'] is None, 'Pump inherited overflow diagnostic correction')
        expected_notice = dict(cases=1, executions=3, signature_fields=6, actual_captured_loads=3, parent_notice_differences=1, candidate_notice_differences=0, strict_ordered_log_mismatches=0, source_normalization=None)
        require(report['program_creator_notice'] == selected['program_creator_notice'] == expected_notice, 'Pump bounded executable-creator notice correction')
        for key, path in [('source_recipe', '/build.py'), ('source_builder', '/build.py'), ('source_binding_verifier', '/verify.py'), ('comparison_report', '/builds/cold-01/build-comparison.json'), ('build_log', '/builds/cold-01/build.log'), ('validation_report', '/runtime/full44.json.gz'), ('strict_ordered_log_report', '/runtime/full44.strict-logs.json')]:
            require(selected[key] == notice + path and (root / selected[key]).is_file(), 'Pump notice selected ' + key)
        from pump_strict_ordered_logs import audit as audit_strict_logs
        import gzip
        checker = root / 'scripts/pump_strict_ordered_logs.py'
        require(sha(checker) == selected['strict_ordered_log_checker_sha256'] == '459b40e04a730f01f257005ed705a4f7d576c04f55acd4eca6a3d37c5326cf5e', 'Pump strict ordered-log checker')
        strict = audit_strict_logs(json.loads(gzip.decompress((root / selected['validation_report']).read_bytes())), candidate, 10468)
        saved = json.loads((root / selected['strict_ordered_log_report']).read_text())
        require(all(saved[key] == value for key, value in strict.items()) and saved['source_report_sha256'] == sha(root / selected['validation_report']) and saved['checker_sha256'] == sha(checker), 'Pump notice saved strict log audit')
        require(strict['strict_ordered_log_mismatch_cases'] == 0 and selected['strict_ordered_log_pairs'] == strict['case_pairs'] == 10468, 'Pump notice unchanged Source/log scope')
        prior = selected['prior_closure_selection']
        require(sha(root / prior['path']) == prior['sha256'], 'Pump prior selection history')
        for gap in selected['historical_behavior_gaps']:
            require(sha(root / gap['report']) == gap['sha256'] and gap['candidate_sha256'] in {'acc5e6eba8c9295386443542847404e55a27d8e837402fb98de8ccffb679125f', '199fd7379b6881adefd9e54803f75902176c17bded1718bfc1c59b1cf5bc8473', 'c0e29e2d41c30e854f3548b37e87798d516e4e0e7769f40b7d8d16e31429795f'}, 'Pump historical failure evidence')
        require(selected['known_behavior_gaps'] == [] and not selected['full_byte_equality'] and not selected['meaningful_elf_equal'] and not report['whole_elf_equal'] and report['goal_complete'] is False and selected.get('goal_complete', False) is False, 'Pump incomplete reconstruction scope')
        return {**report, 'status': 'PASS', 'current_source_verified': True, 'independent_builds': 2, 'portable_empty_target_build': True, 'known_behavior_gaps': []}
    accrual = 'research/pump-multihop-accrual-qualification-20261028'
    if selected['candidate_artifact'] == accrual + '/artifacts/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / accrual
        seal = 'd5a7e29ae52b385453e055cc619a1bee700f646123e86507daf35d9be5a2c9dd'
        require(sha(packet / 'MANIFEST.json') == selected['candidate_packet_manifest_sha256'] == selected['checkpoint_manifest_sha256'] == seal, 'Pump accrual qualification seal')
        result = subprocess.run([sys.executable, '-B', str(packet / 'verify.py'), '--source-directory', str(root / 'programs/pump')], cwd=root, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        require(report['passed'] and report['sealed'], 'Pump sealed accrual qualification')
        candidate = 'c0e29e2d41c30e854f3548b37e87798d516e4e0e7769f40b7d8d16e31429795f'
        symbols = 'dd73afe77d90d289e9383ee1aa12cdb26608752eb1a1f8b3a4135c0af786cb17'
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']) == candidate, 'Pump accrual selected executable')
        require(selected['candidate_symbols_artifact'] == accrual + '/artifacts/unstripped.so' and selected['symbols_sha256'] == sha(root / selected['candidate_symbols_artifact']) == symbols, 'Pump accrual selected symbols')
        require(selected['canonical_source_inputs'] == len(json.loads((packet / 'SOURCE65.json').read_text())) == 65 and selected['materialized_workspace_inputs'] == 66, 'Pump accrual compiler source scope')
        require(report['normalized'] == selected['normalized_function_matches'] == 1019 and report['raw'] == selected['raw_function_matches'] == 188 and report['window_gain'] == 0, 'Pump unchanged complete-window scope')
        require(report['actual_builds'] == 2 and report['cold_empty_target'] and selected['portable_empty_target_build'], 'Pump actual matching warm and cold builds')
        full, focus, captured = report['full44'], report['focused'], report['captured_create']
        require(full['pairs'] == selected['validated_cases'] == 10468 and full['transaction_fields'] == selected['runtime_transaction_fields'] == 18343 and full['signature_fields'] == selected['verified_transaction_signatures'] == 27875, 'Pump accrual full runtime scope')
        require(focus['strict_case_records'] == selected['focused_runtime_cases'] == 106 and focus['strict_outcome_executions'] == selected['focused_runtime_transactions'] == 318 and focus['strict_signature_fields_verified'] == selected['focused_runtime_signature_fields'] == 465, 'Pump accrual focused scope')
        require(focus['legacy_case_pairs'] == selected['legacy_runtime_cases'] == 284 and focus['legacy_signature_fields_verified'] == selected['legacy_runtime_signature_fields'] == 568, 'Pump accrual legacy scope')
        require(focus['extension_case_pairs'] == selected['extension_runtime_cases'] == 126 and focus['extension_signature_fields_verified'] == selected['extension_runtime_signature_fields'] == 252, 'Pump accrual extension scope')
        require(captured['cases'] == selected['captured_create_cases'] == 14 and captured['executions'] == captured['actual_captured_loads'] == 42 and captured['signature_fields'] == selected['captured_create_signature_fields'] == 84 and captured['source_normalization'] is None, 'Pump accrual captured creation supplement')
        require(selected['captured_create_packet_manifest_sha256'] == seal and report['counter_cases'] == selected['accrual_counter_cases'] == 12 and report['counter_executions'] == selected['accrual_counter_executions'] == 36 and report['parent_Source_differences'] == 3 and report['source_normalization'] is None, 'Pump actual overflow diagnostic correction')
        for key, path in [('source_recipe', '/build.py'), ('source_builder', '/build.py'), ('source_binding_verifier', '/verify.py'), ('comparison_report', '/builds/cold-01/build-comparison.json'), ('build_log', '/builds/cold-01/build.log'), ('validation_report', '/runtime/full44.json.gz'), ('strict_ordered_log_report', '/runtime/full44.strict-logs.json')]:
            require(selected[key] == accrual + path and (root / selected[key]).is_file(), 'Pump accrual selected ' + key)
        from pump_strict_ordered_logs import audit as audit_strict_logs
        import gzip
        checker = root / 'scripts/pump_strict_ordered_logs.py'
        require(sha(checker) == selected['strict_ordered_log_checker_sha256'] == '459b40e04a730f01f257005ed705a4f7d576c04f55acd4eca6a3d37c5326cf5e', 'Pump strict ordered-log checker')
        strict = audit_strict_logs(json.loads(gzip.decompress((root / selected['validation_report']).read_bytes())), candidate, 10468)
        saved = json.loads((root / selected['strict_ordered_log_report']).read_text())
        require(all(saved[key] == value for key, value in strict.items()) and saved['source_report_sha256'] == sha(root / selected['validation_report']) and saved['checker_sha256'] == sha(checker), 'Pump accrual saved strict log audit')
        require(strict['strict_ordered_log_mismatch_cases'] == 0 and selected['strict_ordered_log_pairs'] == strict['case_pairs'] == 10468, 'Pump accrual unchanged Source/log scope')
        prior = selected['prior_closure_selection']
        require(sha(root / prior['path']) == prior['sha256'], 'Pump prior selection history')
        for gap in selected['historical_behavior_gaps']:
            require(sha(root / gap['report']) == gap['sha256'] and gap['candidate_sha256'] in {'acc5e6eba8c9295386443542847404e55a27d8e837402fb98de8ccffb679125f', '199fd7379b6881adefd9e54803f75902176c17bded1718bfc1c59b1cf5bc8473'}, 'Pump historical failure evidence')
        require(selected['known_behavior_gaps'] == [] and not selected['full_byte_equality'] and not selected['meaningful_elf_equal'] and not report['whole_elf_equal'] and not report['goal_complete'], 'Pump incomplete reconstruction scope')
        return {**report, 'status': 'PASS', 'current_source_verified': True, 'independent_builds': 2, 'portable_empty_target_build': True, 'known_behavior_gaps': []}
    final = 'research/pump-final-composition-673-20261028'
    if selected['candidate_artifact'] == final + '/artifacts/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / final
        cold = root / 'research/pump-final-composition-cold-20261028'
        require(sha(packet / 'MANIFEST.json') == selected['candidate_packet_manifest_sha256'] == '02646818f7a4d79b8c99daaa892a210f83f21e8995082f4082fa8cd9440404e4', 'Pump final composition seal')
        require(sha(cold / 'manifest.json') == selected['checkpoint_manifest_sha256'] == 'df461b8b5fd3ca0be4c842de1e8ab84cbb150a7b5f5fd89de26056d7dd3ea1f1', 'Pump actual empty-target repeat seal')
        # This sealed component explicitly rejects optimized Python. Its child
        # always runs normally, including when this public entry point uses -O.
        result = subprocess.run([sys.executable, '-B', str(packet / 'verify.py'), '--source-directory', str(root / 'programs/pump'), '--signatures'], cwd=root, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']) == '199fd7379b6881adefd9e54803f75902176c17bded1718bfc1c59b1cf5bc8473', 'Pump final selected executable')
        require(selected['candidate_symbols_artifact'] == final + '/artifacts/unstripped.so' and report['unstripped_sha256'] == selected['symbols_sha256'] == sha(root / selected['candidate_symbols_artifact']) == '49df399b8a36a0a60de03e8d55f1417261dc451e44845ca9d17a94040968c680', 'Pump final selected symbols')
        import gzip
        require(gzip.decompress((packet / 'historical/original.so.gz').read_bytes()) == (root / 'evidence/original/pump/deployed.so').read_bytes(), 'Pump unchanged captured original')
        require(report['source_files'] == selected['canonical_source_inputs'] == 65 and selected['materialized_workspace_inputs'] == 66, 'Pump final compiler source scope')
        require(report['normalized_windows'] == selected['normalized_function_matches'] == 1019 and report['raw_windows'] == selected['raw_function_matches'] == 188, 'Pump final complete window memberships')
        require(report['broad_case_pairs'] == selected['validated_cases'] == 10468 and report['broad_signature_fields'] == selected['verified_transaction_signatures'] == 27875, 'Pump final broad runtime scope')
        require(report['strict_focused_cases'] == selected['focused_runtime_cases'] == 106 and report['strict_focused_transactions'] == selected['focused_runtime_transactions'] == 318 and report['strict_focused_signature_fields'] == selected['focused_runtime_signature_fields'] == 465, 'Pump final strict focused scope')
        require(report['legacy_cases'] == selected['legacy_runtime_cases'] == 284 and report['legacy_signature_fields'] == selected['legacy_runtime_signature_fields'] == 568, 'Pump final strict legacy scope')
        focus = json.loads((packet / 'FOCUSED-VERIFIED.json').read_text())
        require(focus['extension_case_pairs'] == selected['extension_runtime_cases'] == 126 and focus['extension_signature_fields_verified'] == selected['extension_runtime_signature_fields'] == 252, 'Pump final extension scope')
        for key, path in [('source_recipe', final + '/build.py'), ('source_builder', final + '/build.py'), ('source_binding_verifier', final + '/verify.py'), ('comparison_report', 'research/pump-final-composition-cold-20261028/builds/cold-01/build-comparison.json'), ('build_log', 'research/pump-final-composition-cold-20261028/builds/cold-01/build.log'), ('validation_report', final + '/runtime/full44.json.gz')]:
            require(selected[key] == path and (root / path).is_file(), 'Pump final selected ' + key)
        captured_packet = root / 'research/pump-create-captured-successor-20261028'
        require(sha(captured_packet / 'MANIFEST.json') == selected['captured_create_packet_manifest_sha256'] == '34ee132b379303b05c0a49439319e59cd0212a76818a3d9b5fd36baa89b318a1', 'Pump captured creation supplement seal')
        captured = json.loads(subprocess.check_output([sys.executable, '-O', '-B', str(captured_packet / 'verify.py')], cwd=root, text=True))
        require(captured['candidate_sha256'] == report['candidate_sha256'] and captured['cases'] == selected['captured_create_cases'] == 14 and captured['normally_signed_executions'] == captured['captured_pump_loads'] == 42 and captured['signature_fields_verified'] == selected['captured_create_signature_fields'] == 84 and captured['candidate_structured_or_strict_source_differences'] == 0, 'Pump captured creation scope')
        strict_checker = root / 'scripts/pump_strict_ordered_logs.py'
        require(sha(strict_checker) == selected['strict_ordered_log_checker_sha256'] == '459b40e04a730f01f257005ed705a4f7d576c04f55acd4eca6a3d37c5326cf5e', 'Pump strict ordered-log checker')
        from pump_strict_ordered_logs import audit as audit_strict_logs
        raw_report = (root / selected['validation_report']).read_bytes()
        strict = audit_strict_logs(json.loads(gzip.decompress(raw_report)), report['candidate_sha256'], 10468)
        saved = json.loads((root / selected['strict_ordered_log_report']).read_text())
        require(all(saved[key] == value for key, value in strict.items()) and saved['source_report_sha256'] == sha(root / selected['validation_report']) and saved['checker_sha256'] == sha(strict_checker), 'Pump saved strict ordered-log audit')
        require(strict['strict_ordered_log_mismatch_cases'] == 0 and selected['strict_ordered_log_pairs'] == strict['case_pairs'] == 10468, 'Pump unmasked Source/ordered-log scope')
        prior = selected['prior_closure_selection']
        require(sha(root / prior['path']) == prior['sha256'], 'Pump prior selection history')
        for gap in selected['historical_behavior_gaps']:
            require(sha(root / gap['report']) == gap['sha256'] and gap['candidate_sha256'] == 'acc5e6eba8c9295386443542847404e55a27d8e837402fb98de8ccffb679125f', 'Pump historical failure evidence')
        require(selected['known_behavior_gaps'] == [] and selected['full_byte_equality'] is False and selected['meaningful_elf_equal'] is False and selected['portable_empty_target_build'] is True, 'Pump final qualification scope')
        return {**report, 'status': 'PASS', 'current_source_verified': True, 'portable_empty_target_build': True, 'independent_builds': 3, 'captured_create': captured, 'strict_ordered_log_pairs': strict['case_pairs'], 'strict_ordered_log_mismatches': 0, 'known_behavior_gaps': [], 'goal_complete': False}
    successor = 'research/pump-create-used-boundaries-20261028'
    if selected['candidate_artifact'] == successor + '/artifacts/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        proof = root / 'research/pump-create-portable-repeat-20261028'
        require(sha(proof / 'manifest.json') == selected['checkpoint_manifest_sha256'] == '1d6870ccdc246852ff39cc17b781a2766e6b45dc5fc8eae7101c6b8975aa2409', 'Pump executed portable proof seal')
        require(sha(root / successor / 'MANIFEST.json') == 'bb76099bd1956b83889c66f7e794ba5c251f46d85a5dfc624c8775dd9b0d89af', 'Pump used-boundary source proof seal')
        result = subprocess.run([sys.executable, '-B', str(proof / 'verify.py'), '--repo', str(root)], cwd=root, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']), 'Pump selected successor image')
        require(selected['candidate_symbols_artifact'] == successor + '/artifacts/unstripped.so' and report['symbols_sha256'] == selected['symbols_sha256'] == sha(root / selected['candidate_symbols_artifact']), 'Pump selected successor symbols')
        require(report['normalized_windows'] == selected['normalized_function_matches'] == 1019 and report['raw_windows'] == selected['raw_function_matches'] == 188, 'Pump successor membership')
        require(report['runtime_cases'] == selected['validated_cases'] == 10468 and report['focused_cases'] == selected['focused_runtime_cases'] == 75, 'Pump successor runtime scope')
        require(report['runtime_signature_fields'] == selected['verified_transaction_signatures'] == 27875 and report['focused_signature_fields'] == selected['focused_runtime_signature_fields'] == 318, 'Pump successor signature scope')
        require(report['current_source_verified'] and report['portable_empty_target_build'] and selected['full_byte_equality'] is False, 'Pump successor source/build scope')
        for gap in selected.get('known_behavior_gaps', []):
            require(sha(root / gap['report']) == gap['sha256'] and gap['candidate_sha256'] == report['candidate_sha256'], 'Pump known behavior gap binding')
        return {**report, 'known_behavior_gaps': selected.get('known_behavior_gaps', [])}
    current = 'repro/pump/canonical-frontier-20261028'
    if selected['candidate_artifact'] == current + '/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / current
        seal = '3a4a8541cf82e5c0da0963c81f34e6a1c4de9ec6544d54052194e2020bbe2394'
        require(sha(packet / 'MANIFEST.json') == selected['checkpoint_manifest_sha256'] == seal, 'Pump canonical packet seal')
        # This sealed component explicitly rejects optimized Python. Launch a
        # normal interpreter so its historical assertions remain active.
        result = subprocess.run([sys.executable, '-B', str(packet / 'verify.py'), '--repo', str(root), '--signatures'], cwd=root, capture_output=True, text=True, check=True)
        report = json.loads(result.stdout)
        require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root / selected['candidate_artifact']), 'Pump selected executable')
        require(selected['candidate_symbols_artifact'] == current + '/unstripped.so', 'Pump selected symbol path')
        require(sha(root / selected['candidate_symbols_artifact']) == selected['symbols_sha256'], 'Pump selected symbols')
        require(report['normalized_windows'] == selected['normalized_function_matches'] == 1019 and report['raw_windows'] == selected['raw_function_matches'] == 188, 'Pump selected window counts')
        require(report['runtime_cases'] == selected['validated_cases'] == 10468 and report['focused_runtime_cases'] == 65, 'Pump selected runtime scope')
        require(report['portable_empty_target_build'] is True and selected['full_byte_equality'] is False, 'Pump reconstruction scope')
        require(report['runtime_transactions'] == selected['runtime_transaction_fields'] == 18343 and report['runtime_signature_fields'] == selected['verified_transaction_signatures'] == 27875, 'Pump retained signature scope')
        require(report['focused_transactions'] == selected['focused_runtime_transactions'] == 195 and report['focused_signature_fields'] == selected['focused_runtime_signature_fields'] == 258, 'Pump focused signature scope')
        for key, relative in [('source_recipe', '/compose.py'), ('source_builder', '/build.py'), ('build_log', '/portable-build/build.log.gz'), ('validation_report', '/runtime/full44.json.gz')]:
            require(selected[key] == current + relative and (root / selected[key]).is_file(), 'Pump selected ' + key)
        return {'status': 'PASS', 'actual_current_sources_checked': True, 'goal_complete': False, **report}
    package = root / PACKAGE
    def require(value, message):
        # Explicit check instead of `assert`: `python -O` / PYTHONOPTIMIZE
        # strips asserts, which made tampered main-checkpoint evidence
        # report PASS. Mirrors the sealed branches above.
        if not value:
            raise ValueError(message)
    require(sha(package / 'MANIFEST.json') == MANIFEST_SHA256, 'Pump main checkpoint seal')
    checkpoint = json.loads((package / 'CHECKPOINT.json').read_text())
    status = json.loads((root / 'repro/status.json').read_text())['pump']
    require(status['candidate_artifact'] == PACKAGE + '/candidate.so', 'Pump main checkpoint selection')
    require(status['candidate_sha256'] == checkpoint['candidate_sha256'], 'Pump main checkpoint candidate')
    require(status['symbols_sha256'] == checkpoint['unstripped_sha256'], 'Pump main checkpoint symbols')
    require(not status['full_byte_equality'] and not checkpoint['goal_complete'], 'Pump main checkpoint scope')
    for name, expected in checkpoint['primary_source_sha256'].items():
        path = root / 'programs/pump' / name
        require(not path.is_symlink() and sha(path) == expected, name)
    compiled_inputs = source_manifest(root / 'programs/pump', root / 'programs/pump', root)
    actual = {str((root / name).relative_to(root / 'programs/pump')) for name in compiled_inputs}
    require(actual == set(checkpoint['primary_source_sha256']), 'Pump main checkpoint source scope')
    subprocess.run([sys.executable, '-B', str(package / 'verify.py')],
                   cwd=root, check=True)
    return {'status': 'PASS', 'program': 'pump',
            'candidate_sha256': checkpoint['candidate_sha256'],
            'source_files': len(actual),
            'normalized_windows': checkpoint['normalized_windows'],
            'original_windows': checkpoint['original_windows'],
            'whole_elf_equal': False, 'goal_complete': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo), indent=2))
