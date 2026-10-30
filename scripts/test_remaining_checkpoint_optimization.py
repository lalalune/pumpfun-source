"""The remaining-guards checkpoint verifier must reject tampered evidence in every
optimization mode.

`python -O` / `-OO` strip `assert`, and every acceptance check in
scripts/verify_pump_remaining_checkpoint.py is an assert, so a synthetic root
whose status report names a wrong candidate digest (and zero validated cases)
is rejected under plain python but prints PASS under -O/-OO. The fixture
supplies every file the verifier reads outside its asserts, including a
materialize.py that populates the inner directory, so the only difference
between the modes is whether the checks run.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'verify_pump_remaining_checkpoint.py'
MAIN = 'repro/pump/remaining-guards-main-fortyeight'
SCRATCH = 'repro/pump/remaining-guards-fortyeight'

MATERIALIZE = """import argparse
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--expected-seal')
parser.add_argument('--output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
for name in ('candidate.so', 'unstripped.so', 'verify.py', 'manifest.sha256'):
    (args.output / name).write_bytes(b'tampered bytes\\n')
(args.output / 'manifest.json').write_text('{}', encoding='utf-8')
"""


def fixture(root):
    for package in (MAIN, SCRATCH):
        directory = root / package
        directory.mkdir(parents=True)
        (directory / 'manifest.json').write_text('{}', encoding='utf-8')
        (directory / 'manifest.sha256').write_bytes(b'not a sidecar\n')
    main, wrapper = root / MAIN, root / SCRATCH
    (root / 'repro' / 'status.json').write_text(json.dumps({'pump': {
        'candidate_artifact': MAIN + '/main/candidate.so',
        'comparison_report': MAIN + '/main/build-comparison.json',
        'build_log': MAIN + '/main/build.log',
        'candidate_sha256': '0' * 64,
        'validated_cases': 0,
    }}), encoding='utf-8')
    (main / 'main').mkdir(parents=True)
    for path in (main / 'main' / 'candidate.so', main / 'main' / 'unstripped.so',
                 wrapper / 'inner-manifest.json', wrapper / 'inner-reader.py'):
        path.write_bytes(b'tampered bytes\n')
    (main / 'main' / 'build-comparison.json').write_text(
        json.dumps({'source_sha256': {}}), encoding='utf-8')
    (main / 'main' / 'README.final.md').write_text('tampered\n', encoding='utf-8')
    (main / 'promotion-control').mkdir(parents=True)
    (main / 'promotion-control' / 'inputs.json').write_text(
        json.dumps({'helpers': {}, 'scratch_seal': '0' * 64}), encoding='utf-8')
    (main / 'verify.py').write_text('', encoding='utf-8')
    (wrapper / 'materialize.py').write_text(MATERIALIZE, encoding='utf-8')
    (root / 'programs' / 'pump').mkdir(parents=True)
    (root / 'programs' / 'pump' / 'README.md').write_text('tampered\n', encoding='utf-8')
    (root / 'scripts').mkdir(parents=True)
    shutil.copyfile(ROOT / 'scripts' / 'build_source_manifest.py',
                    root / 'scripts' / 'build_source_manifest.py')


class RemainingCheckpointOptimizationTests(unittest.TestCase):
    def run_verifier(self, root, flags):
        return subprocess.run(
            [sys.executable, '-B', *flags, str(SCRIPT), '--repo', str(root)],
            capture_output=True, text=True, timeout=60)

    def test_tampered_status_is_rejected_in_every_mode(self):
        for flags in ([], ['-O'], ['-OO']):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                result = self.run_verifier(root, flags)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn("'status': 'PASS'", result.stdout)


if __name__ == '__main__':
    unittest.main()
