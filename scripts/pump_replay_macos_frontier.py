#!/usr/bin/env python3
"""Restore native macOS artifacts and run their own complete offline corpus."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
from pathlib import Path
import gzip
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
import pump_validate_all as corpus

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'work/pump-macos-frontier-inputs'
BUILD = ROOT / 'work/pump-macos-qualification/candidate'
OUT = ROOT / 'work/pump-macos-frontier-runtime/evidence'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def staging_dir(parent, name):
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='.' + name + '-', dir=parent))


def bind_relocated_sources(record, source, origin):
    """Verify archived workspace bytes and derive an execution-time receipt.

    The original build receipt remains byte-for-byte intact. Only its known
    workspace prefix moves; repository-level compiler inputs keep their names.
    """
    prefix = (BUILD / 'source').relative_to(ROOT)
    sources = {}
    for name, digest in record['source_sha256'].items():
        path = Path(name)
        if path.is_relative_to(prefix):
            path = source / path.relative_to(prefix)
        else:
            path = ROOT / path
        assert sha(path) == digest, 'restored compiler input differs: ' + name
        sources[path.relative_to(ROOT).as_posix()] = digest
    return {
        **record,
        'source_directory': str(source / 'programs/pump'),
        'source_sha256': sources,
        'replay_source_binding': {
            'kind': 'verified-workspace-relocation',
            'origin_build_record': origin.relative_to(ROOT).as_posix(),
            'origin_build_record_sha256': sha(origin),
            'original_compiled_source_sha256': record['source_sha256'],
            'original_workspace_prefix': prefix.as_posix(),
            'execution_workspace_prefix': source.relative_to(ROOT).as_posix(),
        },
    }


def preserve_failure(build, output, error):
    failures = OUT.parent / 'failures'
    failures.mkdir(parents=True, exist_ok=True)
    attempt = Path(tempfile.mkdtemp(prefix='attempt-', dir=failures))
    if build.exists():
        build.rename(attempt / 'candidate')
    if output.exists():
        output.rename(attempt / 'evidence')
    (attempt / 'failure.json').write_text(json.dumps({
        'status': 'failed',
        'complete': False,
        'error_type': type(error).__name__,
        'error': str(error),
        'candidate_retained': (attempt / 'candidate').is_dir(),
        'evidence_retained': (attempt / 'evidence').is_dir(),
    }, indent=2) + '\n',encoding='utf-8',newline='\n')
    return attempt


def publish(build, output):
    if BUILD.exists() or OUT.exists():
        raise FileExistsError('refusing to replace an existing replay packet')
    BUILD.parent.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build.rename(BUILD)
    try:
        output.rename(OUT)
    except BaseException:
        BUILD.rename(build)
        raise


def main():
    if BUILD.exists() or OUT.exists():
        raise FileExistsError('refusing to replace an existing replay packet')
    build = staging_dir(BUILD.parent, 'candidate')
    output = staging_dir(OUT.parent, 'evidence')
    try:
        manifest = json.loads((INPUT / 'MANIFEST.json').read_text())
        assert manifest, 'replay input manifest binds no source'
        assert all(sha(INPUT / name) == digest for name, digest in manifest.items())
        for name in ('candidate.so', 'unstripped.so', 'build-comparison.json',
                     'build-attempt.json'):
            (build / name).write_bytes(gzip.decompress(
                (INPUT / 'candidate' / (name + '.gz')).read_bytes()))
        source = build / 'source'
        source.mkdir()
        with tarfile.open(INPUT / 'candidate/compiled-source.tar.gz') as archive:
            archive.extractall(source, filter='data')
        record = json.loads((build / 'build-comparison.json').read_text())
        assert record['returncode'] == 0 and record['source_unchanged']
        assert sha(build / 'candidate.so') == record['comparison']['candidate_sha256']
        replay_record = bind_relocated_sources(record, source, build / 'build-comparison.json')
        replay_comparison = build / 'replay-build-comparison.json'
        replay_comparison.write_text(json.dumps(replay_record, indent=2) + '\n',
                                     encoding='utf-8', newline='\n')
        binding = {'candidate_sha256': sha(build / 'candidate.so'),
                   'native_artifact_manifest_sha256': sha(INPUT / 'MANIFEST.json'),
                   'native_revision': (INPUT / 'revision.txt').read_text().strip(),
                   'native_build_record_sha256': sha(build / 'build-comparison.json'),
                   'compiled_source_sha256': record['source_sha256'],
                   'replay_build_record_sha256': sha(replay_comparison),
                   'replay_compiled_source_sha256': replay_record['source_sha256']}
        (output / 'native-input-binding.json').write_text(
            json.dumps(binding, indent=2) + '\n',encoding='utf-8',newline='\n')
        subprocess.run([
            sys.executable, '-B', str(ROOT / 'scripts/pump_validate_parallel.py'),
            '--candidate', str(build / 'candidate.so'),
            '--source-directory', str(source / 'programs/pump'),
            '--build-comparison', str(replay_comparison),
            '--workers', '4', '--captured-loader',
            '--output', str(output / 'full.json.gz'),
        ], cwd=ROOT, check=True)
        subprocess.run([
            sys.executable, '-B', str(ROOT / 'scripts/pump_with_captured_loader.py'),
            '--receipt', str(output / 'recipients.loader.json'),
            str(ROOT / 'scripts/pump_buyback_recipient_differential.py'),
            '--candidate', str(build / 'candidate.so'),
            '--output', str(output / 'recipients.json'),
        ], cwd=ROOT, check=True)
        migration_reports = {}
        for label, script, count in [
            ('legacy_migration_quote', 'pump_migration_quote_differential.py', 20),
            ('v2_migration_quote', 'pump_migration_v2_quote_differential.py', 40),
        ]:
            report_path = output / (label + '.json.gz')
            subprocess.run([
                sys.executable, '-B', str(ROOT / 'scripts/pump_with_captured_loader.py'),
                '--receipt', str(output / (label + '.loader.json')),
                str(ROOT / 'scripts' / script), '--candidate', str(build / 'candidate.so'),
                '--output', str(report_path),
            ], cwd=ROOT, check=True)
            report = json.loads(gzip.decompress(report_path.read_bytes()))
            assert report['candidate_sha256'] == binding['candidate_sha256']
            assert report['case_count'] == count and not report['mismatches']
            assert not report['diagnostics']['mismatches']
            assert report['diagnostics']['log_bearing_cases'] == count
            migration_reports[label] = count
        full = json.loads(gzip.decompress((output / 'full.json.gz').read_bytes()))
        recipients = json.loads((output / 'recipients.json').read_text())
        expected_cases = sum(corpus.EXPECTED_CASES.values())
        assert len(full['suites']) == len(corpus.EXPECTED_CASES) and full['case_count'] == expected_cases
        assert not full['mismatches'] and not full['diagnostics']['mismatches']
        # Two legacy-create controls and two legacy-cashback controls have no logs.
        assert full['diagnostics']['log_bearing_cases'] == expected_cases - 4
        assert recipients['case_count'] == 42 and not recipients['mismatches']
        assert full['candidate_sha256'] == recipients['candidate_sha256'] == binding['candidate_sha256']
        (output / 'qualification.json').write_text(json.dumps({
            'status': 'passed', 'candidate_sha256': binding['candidate_sha256'],
            'corpus_suites': len(full['suites']), 'corpus_cases': full['case_count'],
            'targeted_migration_cases': migration_reports,
            'corpus_diagnostic_mismatches': 0, 'targeted_recipient_cases': 42,
            'scope': 'Separate bounded suites; their control cases can overlap. Whole original ELF equality is not established.',
        }, indent=2) + '\n',encoding='utf-8',newline='\n')
        (output / 'MANIFEST.json').write_text(json.dumps({
            path.relative_to(output).as_posix(): sha(path)
            for path in sorted(output.rglob('*')) if path.is_file()
        }, indent=2) + '\n',encoding='utf-8',newline='\n')
        publish(build, output)
    except BaseException as error:
        attempt = preserve_failure(build, output, error)
        print('replay failed; partial packet retained at ' + str(attempt), file=sys.stderr)
        raise


if __name__ == '__main__':
    main()
