#!/usr/bin/env python3
"""Extract the sealed, unchanged focused Fees harness for current-artifact CI."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'repro/pump_fees/sharing-second-pump-cpi-v144'
HISTORICAL_SEAL = '92e0f76ab475510b403d7a32b7654b2dab8ae697a89c6a24add7ed278789bc67'
CURRENT_CHECKPOINTS = {
    'repro/pump_fees/sharing-authorize-main-v144': '4049a50a07bfb8a4c51b95776607e86abc3ca1588a8d29f7dfde769a5ed51135',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def current_binding():
    import verify_current_checkpoint
    status = json.loads((ROOT / 'repro/status.json').read_text())['pump_fees']
    suffix = '/main/candidate.so'
    assert status['candidate_artifact'].endswith(suffix)
    name = status['candidate_artifact'][:-len(suffix)]
    assert name in CURRENT_CHECKPOINTS, ('Unreviewed focused checkpoint', name)
    current = ROOT / name
    assert sha(current / 'manifest.json') == CURRENT_CHECKPOINTS[name]
    bridge = verify_current_checkpoint.verify('pump_fees', ROOT)
    report_path = current / 'main/build-comparison.json'
    assert ROOT / status['comparison_report'] == report_path
    report = json.loads(report_path.read_text())
    source = report['source_sha256']
    assert len(source) == 26
    for name, digest in source.items():
        part = PurePosixPath(name)
        assert not part.is_absolute() and '..' not in part.parts
        assert sha(current / 'source' / name) == digest, name
    candidate = current / 'main/candidate.so'
    assert sha(candidate) == status['candidate_sha256'] == report['comparison']['candidate_sha256'] == bridge['candidate_sha256']
    return source, {'checkpoint': str(current.relative_to(ROOT)),
                    'manifest_sha256': sha(current / 'manifest.json'),
                    'report_sha256': sha(report_path), 'candidate_sha256': sha(candidate),
                    'bridge': bridge}


def prepare(output):
    manifest = json.loads((PACKAGE / 'manifest.json').read_text())
    expected = (PACKAGE / 'manifest.sha256').read_text().split()[0]
    assert sha(PACKAGE / 'manifest.json') == expected == HISTORICAL_SEAL
    archive = PACKAGE / 'runtime-repository.tar.gz'
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest[archive.name]
    current_source, binding = current_binding()
    output.mkdir(parents=True, exist_ok=False)
    count = 0
    with tarfile.open(archive) as source:
        seen = set()
        for member in source:
            path = PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts, member.name
            if not path.parts or path.parts[0] != 'validation-layer':
                continue
            assert not member.issym() and not member.islnk(), member.name
            if member.isdir():
                continue
            assert member.isfile() and member.name not in seen, member.name
            seen.add(member.name)
            target = output.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.extractfile(member).read())
            count += 1
    assert (output / 'validation-layer/harness/fees_donation_business_differential.py').is_file()
    expected_source = json.loads((output / 'validation-layer/corrected-source-sha256.json').read_text())
    assert len(expected_source) == 26
    for name, digest in expected_source.items():
        assert hashlib.sha256((PACKAGE / 'source' / name).read_bytes()).hexdigest() == digest, name
    source_map = output / 'validation-layer/corrected-source-sha256.json'
    (output / 'historical-corrected-source-sha256.json').write_bytes(source_map.read_bytes())
    source_map.write_text(json.dumps(current_source, indent=2) + '\n')
    witness = {'historical_checkpoint': str(PACKAGE.relative_to(ROOT)),
               'historical_manifest_sha256': HISTORICAL_SEAL,
               'historical_archive_sha256': sha(archive),
               'old_source_sha256': expected_source, 'new_source_sha256': current_source,
               'harness_sha256': {str(p.relative_to(output)): sha(p) for p in sorted((output / 'validation-layer/harness').glob('*.py'))},
               'current': binding, 'target_executions': 0}
    (output / 'source-binding-witness.json').write_text(json.dumps(witness, indent=2) + '\n')
    return {'status': 'PASS', 'extracted_files': count, 'source_inputs': 26, 'target_executions': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2))
