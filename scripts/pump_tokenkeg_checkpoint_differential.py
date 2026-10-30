#!/usr/bin/env python3
"""Run unchanged two-curve cases with an authenticated portable source binding."""
import json
from pathlib import Path

import pump_tokenkeg_two_curve_differential as base
from build_source_manifest import source_manifest
from verify_pump_main_checkpoint import MANIFEST_SHA256, PACKAGE, ROOT, sha


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)


original_binding = base.compiled_binding


def portable_binding(candidate, build_report):
    report = json.loads(build_report.read_text())
    binding = report.get('portable_source_binding')
    if binding is None:
        return original_binding(candidate, build_report)
    package = ROOT / PACKAGE
    check(sha(package / 'MANIFEST.json') == MANIFEST_SHA256, "portable binding verification failed: sha(package / 'MANIFEST.json') == MANIFEST_SHA256")
    manifest = json.loads((package / 'MANIFEST.json').read_text())
    check(binding['kind'] == 'verified-equal-canonical-primary-source', "portable binding verification failed: binding['kind'] == 'verified-equal-canonical-primary-source'")
    check(binding['origin_build_record'] == PACKAGE + '/canonical-build.json', "portable binding verification failed: binding['origin_build_record'] == PACKAGE + '/canonical-build.json'")
    origin_path = package / 'canonical-build.json'
    check(sha(origin_path) == manifest['canonical-build.json'] == binding['origin_build_record_sha256'], "portable binding verification failed: sha(origin_path) == manifest['canonical-build.json'] == binding['origi")
    check(sha(package / 'CHECKPOINT.json') == manifest['CHECKPOINT.json'], "portable binding verification failed: sha(package / 'CHECKPOINT.json') == manifest['CHECKPOINT.json']")
    checkpoint = json.loads((package / 'CHECKPOINT.json').read_text())
    origin = json.loads(origin_path.read_text())
    check(origin['returncode'] == 0 and origin['source_unchanged'], "portable binding verification failed: origin['returncode'] == 0 and origin['source_unchanged']")
    check(binding['original_compiled_source_sha256'] == origin['source_sha256'], "portable binding verification failed: binding['original_compiled_source_sha256'] == origin['source_sha256']")
    check(report['comparison'] == origin['comparison'], "portable binding verification failed: report['comparison'] == origin['comparison']")
    check(sha(candidate) == checkpoint['candidate_sha256'] == origin['comparison']['candidate_sha256'], "portable binding verification failed: sha(candidate) == checkpoint['candidate_sha256'] == origin['comparison")
    expected = {'programs/pump/' + name: digest
                for name, digest in checkpoint['primary_source_sha256'].items()}
    check(report['source_sha256'] == expected, "portable binding verification failed: report['source_sha256'] == expected")
    check(base.SOURCE_DIRECTORY == ROOT / 'programs/pump', "portable binding verification failed: base.SOURCE_DIRECTORY == ROOT / 'programs/pump'")
    check(source_manifest(base.SOURCE_DIRECTORY, base.SOURCE_DIRECTORY, ROOT,
                           cwd=base.SOURCE_DIRECTORY) == expected, "portable binding verification failed: source_manifest(base.SOURCE_DIRECTORY, base.SOURCE_DIRECTORY, ROOT,")
    return {'binding_kind': binding['kind'],
            'report': build_report.relative_to(ROOT).as_posix(),
            'report_sha256': sha(build_report),
            'origin_build_record': binding['origin_build_record'],
            'origin_build_record_sha256': sha(origin_path),
            'candidate_sha256': sha(candidate), 'actual_source_sha256': expected}


base.compiled_binding = portable_binding
base.fixture.compiled_binding = portable_binding
original_bindings = base.bindings


def bindings(candidate, report):
    result = original_bindings(candidate, report)
    result['repository_inputs'][Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    return result


base.bindings = bindings

if __name__ == '__main__':
    base.main()
