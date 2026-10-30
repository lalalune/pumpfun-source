#!/usr/bin/env python3
"""Copy the sealed nested-route harness and bind it to the current main build."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from verify_current_checkpoint import verify as verify_checkpoint

ROOT = Path(__file__).resolve().parents[1]
HARNESS_PACKAGE = ROOT / 'repro/pump/buy-mode-order-fortyeight'
HARNESS_SEAL = '84849c316aa1e9c0bb8ae05050480cd641fdd9546e69cf875085f29645bbd3a0'
PREFIX = 'runtime-layer/nested-harness/'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(ok, message="nested runtime check failed"):
    # Explicit check instead of `assert`: `python -O` / `-OO` strips asserts,
    # which let a tampered harness file, a mismatched candidate, or changed
    # staged source pass preparation and still produce a PASS binding record.
    if not ok:
        raise AssertionError(message)


def prepare(output):
    checkpoint = verify_checkpoint('pump', ROOT)
    status = json.loads((ROOT / 'repro/status.json').read_text())['pump']
    candidate = ROOT / status['candidate_artifact']
    main_package = candidate.parent.parent
    check(candidate.name == 'candidate.so' and candidate.parent.name == 'main')
    manifest_path = HARNESS_PACKAGE / 'manifest.json'
    check(sha(manifest_path) == HARNESS_SEAL)
    manifest = json.loads(manifest_path.read_text())
    selected = {name: value for name, value in manifest.items() if name.startswith(PREFIX)}
    check(len(selected) == 6)
    report_path = ROOT / status['comparison_report']
    check(report_path == main_package / 'main/build-comparison.json')
    attempt_path = main_package / 'main/build-attempt.json'
    report = json.loads(report_path.read_text())
    attempt = json.loads(attempt_path.read_text())
    check(attempt['returncode'] == 0 and attempt['source_unchanged'])
    sources = report['source_sha256']
    check(sources == attempt['source_sha256'] == attempt['source_after_sha256'])
    check(len(sources) == 37)
    for name, digest in sources.items():
        path = PurePosixPath(name)
        check(not path.is_absolute() and '..' not in path.parts)
        check(name.startswith('programs/pump/') and sha(ROOT / name) == digest, name)
    check(report['comparison']['candidate_sha256'] == sha(candidate) == checkpoint['candidate_sha256'])
    output.mkdir(parents=True, exist_ok=False)
    copied = {}
    for name, value in selected.items():
        source = HARNESS_PACKAGE / name
        check(not source.is_symlink() and sha(source) == value['sha256'], name)
        relative = PurePosixPath(name[len(PREFIX):])
        check(not relative.is_absolute() and '..' not in relative.parts)
        target = output.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        copied[str(relative)] = sha(target)
    source_map = output / 'expected-source-map.json'
    historical_sha = sha(source_map)
    source_map.write_text(json.dumps(sources, indent=2, sort_keys=True) + '\n')
    record = {
        'status': 'PASS', 'target_executions': 0, 'source_inputs': len(sources),
        'frozen_harness_seal': HARNESS_SEAL, 'copied_harness_sha256': copied,
        'historical_source_map_sha256': historical_sha,
        'current_source_map_sha256': sha(source_map),
        'build_report_sha256': sha(report_path), 'build_attempt_sha256': sha(attempt_path),
        'candidate_sha256': sha(candidate),
        'current_checkpoint': str(main_package.relative_to(ROOT)),
        'scope': 'Only the copied expected source map changes; cases, runtime code and assertions retain their sealed bytes.'
    }
    (output / 'binding-update.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2))
